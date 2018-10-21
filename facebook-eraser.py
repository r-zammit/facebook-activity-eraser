#!/usr/bin/env python
from __future__ import print_function
from selenium import webdriver
from bs4 import BeautifulSoup
from argparse import ArgumentParser
from time import sleep
import getpass
import sys
if sys.version[0] == '3': raw_input=input   # for python 2/3 cross compatibility

class Eraser(object):
    """
    Eraser class to remove Facebook content
    Set up, log in, go to activity page, then repeat delete
    If having trouble, use scroll down method or increase wait time
    Don't forget to quit in the end
    """

    def __init__(self, email, password, wait=1):
        """
        Set up the eraser
        :return: Null
        """
        self.driver = webdriver.Chrome()
        self.email = email
        self.password = password
        self.profile_name = None            # this will end up being the facebook user name
        self.count = 0                      # counter of number of elements deleted
        self.wait = wait
        self.skipped=0
        self.scrollheight=0

    def quit(self):
        """
        Quit the program (close out the browser)
        :return: Null
        """
        self.driver.quit()

    def login(self):
        """
        Log in to Facebook, set profile name
        :return: Null
        """
        self.driver.get('https://www.facebook.com/login/')
        email_element = self.driver.find_element_by_id('email')
        email_element.send_keys(self.email)
        password_element = self.driver.find_element_by_id('pass')
        password_element.send_keys(self.password)
        password_element.submit()

        soup = BeautifulSoup(self.driver.page_source)
        profile_link = soup.find('a', {'title': 'Profile'})
        self.profile_name = profile_link.get('href')[25:]    # link appears as http://www.facebook.com/PROFILE

    def go_to_activity_page(self):
        """
        Go to the activity page and prepare to start deleting
        :return: Null
        """
        if not self.profile_name:
            # the user hasn't logged in properly
            sys.exit(-2)
        # go to the activity page (filter by 'Your Posts')
        activity_link = 'https://www.facebook.com/' + self.profile_name + '/allactivity?privacy_source=activity_log&log_filter=all'
        self.driver.get(activity_link)
        sleep(self.wait)

        # self.driver.find_elements_by_link_text('2014').click()
        # sleep(self.wait)        

    def scroll_down(self):
        """
        Executes JS to scroll down on page.
        Use if having trouble seeing elements
        :return:
        """
        #self.scrollheight += 500
        #print("scrolling to ",self.scrollheight)
        #self.driver.execute_script('window.scrollTo(0, '+str(self.scrollheight)+');')
        self.driver.execute_script('window.scrollBy(0, 350);')
        sleep(self.wait)

    def delete_element(self):
        """
        Find the first available element and delete it
        :return: Null
        """
        try:
            source = self.driver.page_source
            # click hidden from timeline so the delete button shows up
            soup = BeautifulSoup(self.driver.page_source)
            # Priority: highlights, allowed, hidden
            try:
                menu_button = soup.find('a', {'aria-label': 'Highlighted on Timeline'})
                if menu_button is None:
                    menu_button = soup.find('a', {'aria-label': 'Allowed on Timeline'})
                if menu_button is None:
                    menu_button = soup.find('a', {'aria-label': 'Edit'})
                if menu_button is None:
                    menu_button = soup.find('a', {'aria-label': 'Hidden from Timeline'})
                if menu_button is None:
                    menu_button = soup.find('a', {'aria-label': 'Shown on Timeline'})
                menu_element = self.driver.find_element_by_id(menu_button.get('id'))
            except:
                print("Couldn't find menu_button")
                raise
            #get the parent element and make sure it's the right year

            try:
                parent = menu_button.parent
                classname = parent.get('class')
                while 'fbTimelineLogStream' not in classname:
                    parent = parent.parent
                    classname = parent.get('class')
                    if classname == None:
                        classname = []
                        continue
                    
                    
                year = parent.get('id')
                #year = soup.find('div', {'class':'_iqq'}).parent.get('id') #format 'month_2017_10'
            except:
                raise Exception("couldn't get parent class")
            else:
                yr = [int(yr) for yr in year.split("_") if (yr.isdigit() and len(yr) == 4)][0]
                # if yr.isdigit():
                #     year = int(yr) 
                if(yr > 2014):
                    self.skipped+=1
                    #delete the div from html
                    self.driver.execute_script("document.getElementById('"+year+"').remove();")
                    print('[+] Element Skipped (year={year}), ({skipped} in total)'.format(year = year, skipped = self.skipped))
                    print('scrolling down')
                    self.scroll_down()
                    sleep(self.wait)
                    return
            menu_element.click()
            sleep(self.wait)

            # now that the delete button comes up, find the delete link and click
            # sometimes it takes more than one click to get the delete button to pop up
            if menu_button is not None:
                i = 0
                while i < 3:
                    try:
                        self.driver.find_element_by_link_text('Delete').click()
                        break
                    except:
                        exec_type, exec_obj, exec_tb = sys.exc_info()
                        print ('[*] Clicking menu again from exception on line ', exec_tb.tb_lineno)
                        menu_element.click()
                        sleep(self.wait)
                        i += 1
            sleep(self.wait)

            # click the confirm button, increment counter and display success
            
            self.driver.find_element_by_class_name('layerConfirm').click()
            self.count += 1
            print ('[+] Element Deleted ({count} in total)'.format(count=self.count))
            sleep(self.wait)
        except Exception as e:
            exec_type, exec_obj, exec_tb = sys.exc_info()
            print ('[-] Problem finding element, exception on line ',exec_tb.tb_lineno)
            raise
            

if __name__ == '__main__':
    """
    Main section of script
    """
    # set up the command line argument parser
    parser = ArgumentParser(description='Delete your Facebook activity.  Requires Firefox')
    parser.add_argument('--wait', type=float, default=1, help='Explicit wait time between page loads (default 1 second)')
    args = parser.parse_args()

    # execute the script
    email = raw_input("Please enter Facebook login email: ")
    password = getpass.getpass()
    eraser = Eraser(email=email, password=password, wait=args.wait)
    eraser.login()
    eraser.go_to_activity_page()
    # track failures
    fail_count = 0
    while True:
        if fail_count >= 3:
            print ('[*] Scrolling down')
            eraser.scroll_down()
            fail_count = 0
            sleep(5)
        try:
            print ('[*] Trying to delete element')
            eraser.delete_element()
            fail_count = 0
        except (Exception, ) as e:
            exec_type, exec_obj, exec_tb = sys.exc_info()
            print ('[-] Problem finding element, exception on line ',exec_tb.tb_lineno)
            fail_count += 1
            sleep(2)
