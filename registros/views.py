import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Madre, Parto, RecienNacido
from .forms import MadreForm, PartoForm, RecienNacidoForm, PartoCompletoForm
from django.http import JsonResponse, HttpResponse
from datetime import datetime, timedelta
from .excel_export import exportar_datos_excel
from .utils import normalize_rut
from django.views.decorators.http import require_POST
from django.forms.models import model_to_dict

@login_required
def registro_parto(request):
    if request.method == 'POST':
        allow_old = bool(request.POST.get('allow_historico'))
        
        
        form = PartoCompletoForm(request.POST, prefixes=('madre','parto','recien'), allow_old_parto=allow_old)
        if form.is_valid():
            try:
                madre, parto, recien_nacido = form.save()
                parto.created_by = request.user
                parto.save()
                messages.success(request, 'Registro de parto completado exitosamente.')
                return redirect('registros:detalle_parto', parto_id=parto.id)
            except Exception as e:
                messages.error(request, f'Error al guardar el registro: {str(e)}')
        else:
            
            try:
                madre_err = form.madre_form.errors
                parto_err = form.parto_form.errors
                recien_err = form.recien_nacido_form.errors
                err_summary = f"madre={madre_err}, parto={parto_err}, recien={recien_err}"
            except Exception:
                err_summary = str(form.errors)
            
            messages.error(request, 'Formulario inválido. Revise errores en los campos.')
            messages.info(request, 'POST keys: ' + ','.join(list(request.POST.keys())))
            import logging
            logging.getLogger(__name__).debug('Parto form invalid. POST keys=%s errors=%s', list(request.POST.keys()), err_summary)
    else:
        form = PartoCompletoForm(prefixes=('madre','parto','recien'))
        
        madre_create_form = MadreForm()
    
    return render(request, 'registros/registro_parto.html', {
        'form': form,
        'madre_create_form': madre_create_form if 'madre_create_form' in locals() else None,
        'titulo': 'Nuevo Registro de Parto'
    })

@login_required
def lista_partos(request):
    query = request.GET.get('q', '')
    partos = Parto.objects.select_related('madre', 'created_by').order_by('-fecha_hora')
    
    if query:
        partos = partos.filter(
            Q(madre__rut__icontains=query) |
            Q(madre__nombres__icontains=query) |
            Q(madre__apellidos__icontains=query)
        )
    
    paginator = Paginator(partos, 10)
    page = request.GET.get('page')
    partos_paginados = paginator.get_page(page)
    
    return render(request, 'registros/lista_partos.html', {
        'partos': partos_paginados,
        'query': query,
        'titulo': 'Lista de Partos'
    })

@login_required
def detalle_parto(request, parto_id):
    parto = get_object_or_404(Parto.objects.select_related(
        'madre', 'created_by'
    ).prefetch_related('recien_nacidos'), id=parto_id)
    
    return render(request, 'registros/detalle_parto.html', {
        'parto': parto,
        'titulo': f'Parto de {parto.madre}'
    })

@login_required
def editar_parto(request, parto_id):
    parto = get_object_or_404(Parto, id=parto_id)
    if request.method == 'POST':
        
        madre_form = MadreForm(request.POST, instance=parto.madre)
        parto_form = PartoForm(request.POST, instance=parto)
        recien_nacido_form = RecienNacidoForm(
            request.POST,
            instance=parto.recien_nacidos.first()
        )

        
        logger = logging.getLogger(__name__)
        try:
           
            logger.info('editar_parto POST keys: %s', list(request.POST.keys()))
            
            logger.info('Parto id=%s editar: POST preview: %s', parto_id, {k: (v[:120] + '...') if len(v) > 120 else v for k, v in request.POST.items()})
        except Exception:
            pass

        
        madre_ok = madre_form.is_valid()
        parto_ok = parto_form.is_valid()
        recien_ok = recien_nacido_form.is_valid()

        if madre_ok and parto_ok and recien_ok:
            try:
                madre = madre_form.save()
                parto = parto_form.save(commit=False)
                parto.madre = madre
                parto.save()

                recien_nacido = recien_nacido_form.save(commit=False)
                recien_nacido.parto = parto
                recien_nacido.save()

                messages.success(request, 'Registro actualizado exitosamente.')
                return redirect('registros:detalle_parto', parto_id=parto.id)
            except Exception as e:
                logger.exception('Error guardando edición de parto %s', parto_id)
                messages.error(request, f'Error al actualizar el registro: {str(e)}')
        else:
            
            logger.info('editar_parto validation failed for parto id=%s madre_ok=%s parto_ok=%s recien_ok=%s', parto_id, madre_ok, parto_ok, recien_ok)
            
            try:
                logger.info('Madre form errors: %s', madre_form.errors.as_json())
            except Exception:
                logger.info('Madre form errors: %s', madre_form.errors)
            try:
                logger.info('Parto form errors: %s', parto_form.errors.as_json())
            except Exception:
                logger.info('Parto form errors: %s', parto_form.errors)
            try:
                logger.info('Recien form errors: %s', recien_nacido_form.errors.as_json())
            except Exception:
                logger.info('Recien form errors: %s', recien_nacido_form.errors)

            
            messages.error(request, 'No se pudieron guardar los cambios. Corrija los errores mostrados en los formularios.')
            
            for field, errs in madre_form.errors.items():
                for e in errs:
                    messages.warning(request, f'Madre - {field}: {e}')
            for field, errs in parto_form.errors.items():
                for e in errs:
                    messages.warning(request, f'Parto - {field}: {e}')
            for field, errs in recien_nacido_form.errors.items():
                for e in errs:
                    messages.warning(request, f'Recien Nacido - {field}: {e}')
    else:
        madre_form = MadreForm(instance=parto.madre)
        parto_form = PartoForm(instance=parto)
        recien_nacido_form = RecienNacidoForm(
            instance=parto.recien_nacidos.first()
        )
    
    return render(request, 'registros/editar_parto.html', {
        'madre_form': madre_form,
        'parto_form': parto_form,
        'recien_nacido_form': recien_nacido_form,
        'parto': parto,
        'titulo': f'Editar Parto de {parto.madre}'
    })


@login_required
def madre_lookup(request):
    """API simple que devuelve datos de la madre por RUT (formateado o no).

    GET params: rut
    """
    rut = request.GET.get('rut', '')
    if not rut:
        return JsonResponse({'error': 'Rut requerido'}, status=400)
    
    rut_norm = normalize_rut(rut)
    try:
        
        madres = Madre.objects.all()
        madre = None
        for m in madres:
            if m.rut.replace('.', '').replace('-', '').upper() == rut_norm:
                madre = m
                break
        if not madre:
            return JsonResponse({'found': False})
        data = {
            'found': True,
            'rut': madre.rut,
            'nombres': madre.nombres,
            'apellidos': madre.apellidos,
            'fecha_nacimiento': madre.fecha_nacimiento.isoformat() if madre.fecha_nacimiento else None,
            'estado_civil': madre.estado_civil,
            'direccion': madre.direccion,
            'telefono': madre.telefono,
            'prevision': madre.prevision,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def madre_typeahead(request):
    """Return JSON list of matching mothers by partial rut or name."""
    q = request.GET.get('q', '').strip()
    results = []
    if q:
        q_norm = normalize_rut(q)
        qs = Madre.objects.all()
      
        for m in qs:
            m_norm = m.rut.replace('.', '').replace('-', '').upper()
            if q_norm and m_norm.startswith(q_norm):
                results.append({'id': m.id, 'rut': m.rut, 'nombres': m.nombres, 'apellidos': m.apellidos})
                continue
            if q.lower() in m.nombres.lower() or q.lower() in m.apellidos.lower():
                results.append({'id': m.id, 'rut': m.rut, 'nombres': m.nombres, 'apellidos': m.apellidos})
            if len(results) >= 10:
                break
    return JsonResponse({'results': results})


@login_required
@require_POST
def madre_create(request):
    """API para crear una Madre rápidamente desde un modal o AJAX.

    Espera campos del `MadreForm` (sin prefijos). Devuelve JSON con los datos
    de la madre creada o errores en caso de validación.
    """

@login_required
def madre_create_page(request):
    """Página completa para crear una Madre (fallback para la matrona)."""
    if request.method == 'POST':
        form = MadreForm(request.POST)
        if form.is_valid():
            try:
                madre = form.save()
               
                logger = logging.getLogger(__name__)
                logger.info(
                    'Madre creada por %s: RUT=%s, Nombre=%s %s',
                    request.user.username,
                    madre.rut,
                    madre.nombres,
                    madre.apellidos
                )
                messages.success(
                    request,
                    f'Madre creada exitosamente - RUT: {madre.rut}, Nombre: {madre.nombres} {madre.apellidos}'
                )
                
                return redirect(f"{reverse('registros:registro_parto')}?rut={madre.rut}&madre_creada=1")
            except Exception as e:
                logger = logging.getLogger(__name__)
                logger.error('Error al crear madre: %s', str(e))
                messages.error(
                    request,
                    f'Error al crear la madre: {str(e)}'
                )
        else:
            messages.error(
                request,
                'Por favor corrija los errores en el formulario.'
            )
            
            for error in form.non_field_errors():
                messages.warning(request, error)
            
            
            for field in form.fields:
                if field in form.errors:
                    for error in form.errors[field]:
                        messages.warning(
                            request,
                            f'{form.fields[field].label}: {error}'
                        )
    else:
        form = MadreForm()
        rut_prefill = request.GET.get('rut')
        if rut_prefill:
            form.initial['rut'] = rut_prefill

    return render(request, 'registros/madre_create.html', {
        'madre_create_form': form,
        'titulo': 'Crear Madre'
    })

def madre_create(request):
    """API para crear una Madre rápidamente desde un modal o AJAX.

    Espera campos del `MadreForm` (sin prefijos). Devuelve JSON con los datos
    de la madre creada o errores en caso de validación.
    """
    
    from .utils import normalize_rut, format_rut
    rut_raw = request.POST.get('rut', '')
    if rut_raw:
        norm = normalize_rut(rut_raw)
        if norm:
            formatted = format_rut(norm)
            if Madre.objects.filter(rut=formatted).exists():
                return JsonResponse({'created': False, 'errors': {'rut': ['Ya existe una madre con ese RUT.']}}, status=400)

    form = MadreForm(request.POST)
    if form.is_valid():
        madre = form.save()
        data = {
            'id': madre.id,
            'rut': madre.rut,
            'nombres': madre.nombres,
            'apellidos': madre.apellidos,
            'fecha_nacimiento': madre.fecha_nacimiento.isoformat() if madre.fecha_nacimiento else None,
            'estado_civil': madre.estado_civil,
            'direccion': madre.direccion,
            'telefono': madre.telefono,
            'prevision': madre.prevision,
        }
        return JsonResponse({'created': True, 'madre': data})
    else:
       
        return JsonResponse({'created': False, 'errors': form.errors}, status=400)


@login_required
def exportar_partos(request):
    """Exportar partos a Excel dentro de un rango de fechas (GET start/end en formato YYYY-MM-DD).
    Si no se proveen fechas, exporta TODOS los partos disponibles.
    """
    start = request.GET.get('start')
    end = request.GET.get('end')
    
    # Si no se proporcionan fechas, exportar todos los partos (pasar None)
    if not start or not end:
        fecha_inicio = None
        fecha_fin = None
    else:
        try:
            fecha_inicio = datetime.fromisoformat(start).date()
            fecha_fin = datetime.fromisoformat(end).date()
        except ValueError:
            return HttpResponse('Formato de fecha inválido. Use YYYY-MM-DD', status=400)

    return exportar_datos_excel(fecha_inicio, fecha_fin)
