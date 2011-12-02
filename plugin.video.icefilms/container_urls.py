#!/usr/bin/env python

# Links and info about metacontainers.
# Update this file to update the containers.

# Size is in MB

#return dictionary of strings and integers
def get():
          containers = {} 

          #date updated
          containers['date'] = '9/Feb/2011'
          
          #--- Database Meta Container ---# 
          #containers['db_url'] = 'http://www.megaupload.com/?d=U1RTPGQS'
          containers['db_url'] = 'http://www.megaupload.com/?d=YD7U5M71'
                    
          #--- Movie Meta Container ---# 

          #basic container        
          containers['mv_covers_url'] = 'http://www.megaupload.com/?d=X8CMRAK2'
          containers['mv_cover_size'] = 265
          
          containers['mv_backdrop_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'
          containers['mv_backdrop_size'] = 2600
          
          #--- TV   Meta  Container ---#

          #basic container       
          containers['tv_covers_url'] = 'http://www.megaupload.com/?d=QJMWHCQW'        
          containers['tv_cover_size'] = 530

          containers['tv_backdrop_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'
          containers['tv_backdrop_size'] = 832
          
          
          #additional container
          containers['tv_add_url'] = ''
          containers['tv_add_size'] = 0       


          return containers
