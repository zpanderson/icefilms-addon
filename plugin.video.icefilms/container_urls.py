#!/usr/bin/env python

# Links and info about metacontainers.
# Update this file to update the containers.

# Size is in MB

#return dictionary of strings and integers
def get():
          containers = {} 

          #date updated
          containers['date'] = '9/Feb/2011'
          
          #--- Meta Container ---# 
          #containers['db_url'] = 'http://www.megaupload.com/?d=U1RTPGQS'
          containers['db_url'] = 'http://www.megaupload.com/?d=69UXI5Q2'
                    
          #--- Movie Meta Container ---# 

          #basic container        
          containers['mv_covers_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'
          containers['mv_cover_size'] = 230
          
          containers['mv_backdrops_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'
          containers['mv_backdrop_size'] = 230
          
          #additional container
          containers['mv_add_url'] = ''
          containers['mv_add_size'] = 0


          #--- TV   Meta  Container ---#

          #basic container       
          containers['tv_covers_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'        
          containers['tv_cover_size'] = 230

          containers['tv_backdrops_url'] = 'http://www.megaupload.com/?d=CE07S1EJ'
          containers['tv_backdrops_size'] = 230
          
          
          #additional container
          containers['tv_add_url'] = ''
          containers['tv_add_size'] = 0       


          return containers
