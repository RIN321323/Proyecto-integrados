from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Madre
from .utils import normalize_rut, format_rut
from datetime import date, datetime, timedelta
from .forms import PartoCompletoForm


class MadreApiTests(TestCase):
	def setUp(self):
		self.client = Client()
		User = get_user_model()
		self.user = User.objects.create_user('tester', 't@example.test', 'pw')
		self.client.login(username='tester', password='pw')


		numero = 12345678
		dv = Madre.calcular_dv(numero)
		clean = str(numero) + dv
		formatted = format_rut(clean)

		self.madre = Madre.objects.create(
			rut=formatted,
			nombres='Ana',
			apellidos='Perez',
			fecha_nacimiento=date(1990,1,1),
			estado_civil='soltera',
			direccion='Calle Falsa 123',
			telefono='+56 9 1234 5678',
			prevision='fonasa_a',
			created_by=self.user,
		)

	def test_madre_lookup_by_rut(self):
		url = reverse('registros:madre_lookup')

		resp = self.client.get(url, {'rut': self.madre.rut})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		self.assertTrue(data.get('found'))
		self.assertEqual(data.get('nombres'), 'Ana')

	def test_madre_typeahead_by_partial_rut(self):
		url = reverse('registros:madre_typeahead')

		resp = self.client.get(url, {'q': '1234567'})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		results = data.get('results')
		self.assertTrue(any(r['rut'] == self.madre.rut for r in results))

	def test_madre_typeahead_by_name(self):
		url = reverse('registros:madre_typeahead')
		resp = self.client.get(url, {'q': 'Ana'})
		self.assertEqual(resp.status_code, 200)
		data = resp.json()
		results = data.get('results')
		self.assertTrue(any(r['nombres'] == 'Ana' for r in results))

	def test_parto_completo_form_happy_and_reject(self):
		"""Test PartoCompletoForm: success when RN hour within 1 hour; fail when >1 hour."""

		numero = 12345679
		dv = Madre.calcular_dv(numero)
		clean = str(numero) + dv
		formatted = format_rut(clean)


		madre_data = {
			'rut': formatted,
			'nombres': 'Lucia',
			'apellidos': 'Gomez',
			'fecha_nacimiento': '1990-01-01',
			'estado_civil': 'soltera',
			'direccion': 'Calle Test 1',
			'telefono': '+56 9 1111 2222',
			'prevision': 'fonasa_a'
		}


		base_dt = datetime.now() - timedelta(hours=1)
		fecha_hora_str = base_dt.strftime('%Y-%m-%dT%H:%M')

		data_ok = {}
		data_ok.update(madre_data)
		data_ok.update({
			'fecha_hora': fecha_hora_str,
			'tipo_parto': 'vaginal',
			'semanas_gestacion': '38',
			'tipo_anestesia': 'ninguna',
			'complicaciones': '',
			'observaciones': '',
			'hora_nacimiento': (base_dt + timedelta(minutes=30)).strftime('%H:%M'),
			'sexo': 'F',
			'estado': 'vivo',
			'peso': '3.200',
			'talla': '50.0',
			'apgar_1': '8',
			'apgar_5': '9'
		})

		form_ok = PartoCompletoForm(data_ok)
		self.assertTrue(form_ok.is_valid(), msg=str(form_ok.madre_form.errors) + ' ' + str(form_ok.parto_form.errors) + ' ' + str(form_ok.recien_nacido_form.errors))
		madre, parto, rn = form_ok.save()
		self.assertIsNotNone(parto)
		self.assertEqual(rn.parto, parto)


		data_bad = {}
		data_bad.update(madre_data)
		data_bad.update({
			'fecha_hora': fecha_hora_str,
			'tipo_parto': 'vaginal',
			'semanas_gestacion': '38',
			'tipo_anestesia': 'ninguna',
			'complicaciones': '',
			'observaciones': '',
			'hora_nacimiento': (base_dt + timedelta(hours=2)).strftime('%H:%M'),
			'sexo': 'F',
			'estado': 'vivo',
			'peso': '3.200',
			'talla': '50.0',
			'apgar_1': '8',
			'apgar_5': '9'
		})

		form_bad = PartoCompletoForm(data_bad)
		self.assertFalse(form_bad.is_valid())

	def test_registro_parto_integration_post_creates_records(self):
		"""Integration-like test: POST prefixed form data to registro_parto and
		assert a Parto and RecienNacido are created and the response redirects.
		"""
		from django.urls import reverse
		from .models import Parto, RecienNacido
		User = get_user_model()

		numero = 98765432
		dv = Madre.calcular_dv(numero)
		clean = str(numero) + dv
		formatted = format_rut(clean)

		post_url = reverse('registros:registro_parto')
		base_dt = datetime.now() - timedelta(hours=1)
		fecha_hora_str = base_dt.strftime('%Y-%m-%dT%H:%M')

		data = {
			'madre-rut': formatted,
			'madre-nombres': 'IntTest',
			'madre-apellidos': 'User',
			'madre-fecha_nacimiento': '1990-01-01',
			'madre-estado_civil': 'soltera',
			'madre-direccion': 'Calle Int 1',
			'madre-telefono': '+56 9 9999 0000',
			'madre-prevision': 'fonasa_a',
			'parto-fecha_hora': fecha_hora_str,
			'parto-tipo_parto': 'vaginal',
			'parto-semanas_gestacion': '39',
			'parto-tipo_anestesia': 'ninguna',
			'parto-complicaciones': '',
			'parto-observaciones': '',
			'recien-hora_nacimiento': (base_dt + timedelta(minutes=30)).strftime('%H:%M'),
			'recien-sexo': 'F',
			'recien-estado': 'vivo',
			'recien-peso': '3.200',
			'recien-talla': '50.0',
			'recien-apgar_1': '8',
			'recien-apgar_5': '9',
			'recien-observaciones': ''
		}

		self.client.login(username='tester', password='pw')
		resp = self.client.post(post_url, data)

		self.assertIn(resp.status_code, (302, 301))

		self.assertTrue(Parto.objects.filter(madre__rut=formatted).exists())
		self.assertTrue(RecienNacido.objects.filter(parto__madre__rut=formatted).exists())



class MadreCreateAPITests(TestCase):
    """Tests added to validate the madre_create AJAX endpoint."""
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username='tester2', password='testpass')
        self.client.login(username='tester2', password='testpass')

    def test_create_madre_happy_path(self):
        url = reverse('registros:madre_create')
        data = {
            'rut': '12.345.678-5',
            'nombres': 'Test',
            'apellidos': 'Usuario',
            'fecha_nacimiento': '1990-01-01',
            'estado_civil': 'soltera',
            'direccion': 'Calle Falsa 123',
            'telefono': '+56 9 9123 4567',
            'prevision': 'fonasa_a'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        json = response.json()
        self.assertTrue(json.get('created'))
        madre = Madre.objects.filter(rut='12.345.678-5').first()
        self.assertIsNotNone(madre)
        self.assertEqual(madre.nombres, 'Test')

    def test_create_madre_duplicate_rut(self):
        Madre.objects.create(
            rut='12.345.678-5',
            nombres='Existente',
            apellidos='User',
            fecha_nacimiento='1990-01-01',
            estado_civil='soltera',
            direccion='X',
            telefono='+56 9 9123 4567',
            prevision='fonasa_a'
        )
        url = reverse('registros:madre_create')
        data = {
            'rut': '12.345.678-5',
            'nombres': 'Nuevo',
            'apellidos': 'User',
            'fecha_nacimiento': '1990-01-01',
            'estado_civil': 'soltera',
            'direccion': 'Calle',
            'telefono': '+56 9 9123 4567',
            'prevision': 'fonasa_a'
        }
        response = self.client.post(url, data)
 
        self.assertEqual(response.status_code, 400)
        json = response.json()
        self.assertFalse(json.get('created'))
        self.assertIn('rut', json.get('errors', {}))
