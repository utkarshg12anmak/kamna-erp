from django.test import TestCase
from geo.models import State, City, Pincode, Territory, TerritoryMember, TerritoryCoverage

class TerritoryCoverageMaterializationTest(TestCase):
    def test_pincode_member_creates_single_coverage(self):
        s = State.objects.create(code='DL', name='Delhi', is_active=True)
        c = City.objects.create(state=s, name='New Delhi', is_active=True)
        p = Pincode.objects.create(state=s, city=c, code='110001', is_active=True)
        t = Territory.objects.create(code='DL-T', name='T', type='PINCODE')
        TerritoryMember.objects.create(territory=t, pincode=p)
        self.assertEqual(TerritoryCoverage.objects.filter(territory=t).count(), 1)

    def test_city_member_creates_all_city_pincodes(self):
        s = State.objects.create(code='UP', name='UP', is_active=True)
        c = City.objects.create(state=s, name='Meerut', is_active=True)
        p1 = Pincode.objects.create(state=s, city=c, code='250001', is_active=True)
        p2 = Pincode.objects.create(state=s, city=c, code='250002', is_active=True)
        t = Territory.objects.create(code='UP-T', name='T', type='CITY')
        TerritoryMember.objects.create(territory=t, city=c)
        self.assertCountEqual(list(TerritoryCoverage.objects.filter(territory=t).values_list('pincode__code', flat=True)), ['250001','250002'])

    def test_inactive_pincodes_are_excluded(self):
        s = State.objects.create(code='MH', name='MH', is_active=True)
        c = City.objects.create(state=s, name='Mumbai', is_active=True)
        p1 = Pincode.objects.create(state=s, city=c, code='400001', is_active=False)
        t = Territory.objects.create(code='MH-T', name='T', type='PINCODE')
        TerritoryMember.objects.create(territory=t, pincode=p1)
        self.assertEqual(TerritoryCoverage.objects.filter(territory=t).count(), 0)
