import unittest
from item_catalog import app

class ItemCatalogTests(unittest.TestCase):
    def setUp(self):
        self.app_context = app.app_context()
        self.app_context.push()
        self.client = app.test_client()

    def test_home_page(self):
        """ test home/index page is giving 200 back """
        response = self.client.get('/catalogs')
        self.assertTrue(response.status_code == 200)

    def test_new_catalog(self):
        """ test creating new catalog recieves 204 """
        response = self.client.get('/catalogs/new')
        self.assertTrue(response.status_code == 200)

    def test_edit_catalog(self):
        """ test editing a existing catalog name """
        response = self.client.post('/catalogs/new',data = {'name': 'aCatalog'})
        self.assertTrue(response.status_code == 200)

    def test_delete_catalog(self):
        """ test deleting a existing catalog name """
        response = self.client.post('/catalogs/aCatalog/delete')
        self.assertTrue(response.status_code == 200)

    def test_catalog_items_list(self):
        """ test catalog items page is giving 200 back """
        response = self.client.get('/catalogs/aCatalog/items')
        self.assertTrue(response.status_code == 200)

    def test_edit_catalog_items(self):
        """ test catalog items page is giving 200 back """
        response = self.client.post('/catalogs/aCatalog/items/aItem/edit')
        self.assertTrue(response.status_code == 200)

    def tearDown(self):
        self.app_context.pop()


if __name__ == '__main__':
    unittest.main()
