__author__ = 'palmer'
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mcf_standard_browser.settings")
application = get_wsgi_application()

from selenium import webdriver
import unittest
from django.core.urlresolvers import resolve
from standards_review.views import home_page, MCFStandard_list


class URLResolverTest(unittest.TestCase):
    def home_page_test(self):
        found = resolve('/')
        self.assertEqual(found, home_page)

    def standards_list_test(self):
        found = resolve('library/')
        self.assertEqual(found, MCFStandard_list)


class SiteFunction(unittest.TestCase):
    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_get_to_homepage(self):
        # Prasad checks out the homepage
        self.browser.get('http://localhost:8000')
        # He notices the page title and header mention the MCF
        self.assertIn('MCF', self.browser.title)
        # He sees that he can head to 'review', 'library'

    def test_can_see_and_add_standard(self):
        # Heading to the library part of the website '/library/'
        self.browser.get('http://localhost:8000/library/')
        # The root shows a list of the current standards todo: list->table (An)
        table = self.browser.find_element_by_id('id_list_table')
        # Somewhere there's a button to add a new one todo: if user logged in
        button = self.browser.find_element_by_id('add_standard_button')
        # Clicking add takes you to a form '/library/add/
        self.browser.get('http://localhost:8000/library/add/')  # todo: wire this test into the button url
        # Adds a new standard
        # Submitting returns to the home page
        # New standard is visible


if __name__ == '__main__':  # 7
    unittest.main()
