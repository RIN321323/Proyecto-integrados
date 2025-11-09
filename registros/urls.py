from django.urls import path
from . import views
from . import views_reportes

app_name = 'registros'

urlpatterns = [
    path('registro/', views.registro_parto, name='registro_parto'),
    path('lista/', views.lista_partos, name='lista_partos'),
    path('export/', views.exportar_partos, name='exportar_partos'),
    path('api/madre/', views.madre_lookup, name='madre_lookup'),
    path('api/madre_create/', views.madre_create, name='madre_create'),
    path('madre/create/', views.madre_create_page, name='madre_create_page'),
    path('api/madre_typeahead/', views.madre_typeahead, name='madre_typeahead'),
    path('detalle/<int:parto_id>/', views.detalle_parto, name='detalle_parto'),
    path('editar/<int:parto_id>/', views.editar_parto, name='editar_parto'),
    path('reportes/', views_reportes.reporte_rem, name='reporte_rem'),
]