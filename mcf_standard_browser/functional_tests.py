__author__ = 'palmer'

from selenium import webdriver
import unittest

class NewVisitorTest(unittest.TestCase):

    def setUp(self):
        self.browser = webdriver.Firefox()

    def tearDown(self):
        self.browser.quit()

    def test_can_start_a_list_and_retrieve_it_later(self):
        # Prasad checks out the homepage
        self.browser.get('http://localhost:8000')

        # She notices the page title and header mention to-do lists
        self.assertIn('MCF', self.browser.title)

        # She is invited to enter a to-do item straight away

if __name__ == '__main__':  #7
    unittest.main()