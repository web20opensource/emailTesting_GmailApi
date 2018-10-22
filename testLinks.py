import bs4 as bs
import requests

def testLinks(email):
    linksFound = {};
    for url in bs.BeautifulSoup(email,'html.parser').find_all('a'):
        try:
            #discard from the test the tel links
            if ( url.get('href')[0:3] == "tel" ):
                continue
            with requests.head(url.get('href'), allow_redirects=True) as response:
                linksFound[response.url] = response.status_code;
                if response.status_code == 404:
                #Do whatever you want if 404 is found
                  if (response.url.find("http://mysite.com/privacypolicies") > -1 ):
                    print ( response.url.find("http://mysite.com/privacypolicies") , 
                            "continue...")
                    continue
                  else:
                    print ("404 Found!")
                    print (response.url)
                    input("Press Enter to continue...")
                else:
                  #Do your normal stuff here if page is found.
                  #print ("URL: {0} Response: {1} \n".format(url.get('href'), response.status_code ))
                  #exit()
        except Exception as e:
            print ("Could not connect to URL: {0} by the exception {1}".format(url.get('href'), e) )
    #return True
    return linksFound
