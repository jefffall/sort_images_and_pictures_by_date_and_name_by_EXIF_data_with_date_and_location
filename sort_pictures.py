from exif import Image
from geopy.geocoders import Nominatim

from pathlib import Path
import os.path, time
import shutil
import subprocess
import requests
import json


def decimal_coords(coords, ref):
    decimal_degrees = coords[0] + coords[1] / 60 + coords[2] / 3600
    if ref == "S" or ref =='W' :
        decimal_degrees = -decimal_degrees
    return decimal_degrees

def image_coordinates(image_path):

    with open(image_path, 'rb') as src:
        img = Image(src)
    if img.has_exif:
        try:
            img.gps_longitude
            coords = (decimal_coords(img.gps_latitude,
                      img.gps_latitude_ref),
                      decimal_coords(img.gps_longitude,
                      img.gps_longitude_ref))
        except AttributeError:
            return "No Coordinates"
            #print ('No Coordinates')
    else:
        return "No EXIF"
        #print ('The Image has no EXIF information')
        
    return({"imageTakenTime":img.datetime_original, "geolocation_lat":coords[0],"geolocation_lng":coords[1]})


def get_file_date(i):
    
    #creation_time = os.path.getctime(str(i))
    creation_time = os.stat(str(i)).st_birthtime # MacOS specific
    #print (str(i))
    # Convert the creation time to a readable format
    #print (str(creation_time))
    creation_time_readable = str(time.ctime(creation_time)).strip()
    mydate = creation_time_readable.replace("  "," ")
    
    
    # Mon Jan 25 10:29:41 2021
    parts = mydate.split(" ")
    #print (parts)
    month = parts[1]
    year = parts[4]
    #print (day, month, year)
    return year, month

def get_exif_date(mypath):
    year = ""
    month = ""
    jpgfile = "'"+str(mypath)
    jpgfile = jpgfile+"'"
                
    mycommand = "/usr/local/bin/exiftool -DateTimeOriginal "+jpgfile
            
    result = subprocess.run([mycommand], shell=True, capture_output=True, text=True)
                
    if result.stderr != "":
        print ("error = ",result.stderr)
    if result.stdout != "":
        parts = result.stdout.split(":")
        try:
            year = parts[1].strip()
            month = parts[2].strip()
        except:
            year = ""
            month = ""
            return year, month
        
    mymonth = ['zero','Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
    
    if month != "" and year != "":   
        return year, mymonth[int(month)]
    else:
        return year, month
                    
def get_filename(myfile):
    parts = str(myfile).split("/")
    mylen = len(parts)
    return parts[mylen - 1]

def process_file(i, mysorted, sort_type, new_filename):
    file_sorted = False
    if sort_type == "pictures":
        year, month = get_exif_date(i)
        # EXIF date not found
        if year == "" and month == "":
            # Use the date of the file from the OS
            year, month = get_file_date(i)
    else:
        year, month = get_file_date(i)
    wanted_folder = os.path.exists(mysorted+"/"+year+"_"+month)
           
    if not wanted_folder:
        os.mkdir(mysorted+"/"+year+"_"+month)
            
    if not os.path.isfile(mysorted+"/"+year+"_"+month+"/"+get_filename(i)):
        if new_filename != "":
            original_filename = get_filename(i)
            extension = original_filename[-4:]
            enhanced_filename = new_filename + extension
            print ("cp "+str(i)+" "+mysorted+"/"+year+"_"+month+"/"+enhanced_filename) 
            shutil.copy2(i, mysorted+"/"+year+"_"+month+"/"+enhanced_filename)
        else:
            print ("cp "+str(i)+" "+mysorted+"/"+year+"_"+month+"/"+get_filename(i))    
            shutil.copy2(i, mysorted+"/"+year+"_"+month)
        file_sorted = True
    return file_sorted


def long_lat_to_address(long, lat):
    
    url = "https://nominatim.openstreetmap.org/reverse?lat="+str(lat)+"&lon="+str(long)+"&format=json"
  
    r = requests.get(url, headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    json_addr = r.content.decode()
    addr = json.loads(json_addr)
    
    myclass = ""
    type = ""
    addresstype = ""
    display_name = ""
    name = ""
    house_number = ""
    road = ""
    city = ""
    postcode = ""
    county = ""
    state = ""
    country = ""
    
    try:
        myclass = addr['class']
    except:
        pass
    
    try:
        type = addr['type']
    except:
        pass
    
    try:
        addresstype = addr['addresstype'].strip()
    except:
        pass
        
    try:
        name = addr['name'].strip()
    except:
        pass
    
    try:
        display_name = addr['display_name'].strip()
    except:
        pass
        
    try:
        house_number = addr['address']['house_number'].strip()
    except:
        pass
        
    try:
        road = addr['address']['road'].strip()
    except:
        pass
        
    try:
        city = addr['address']['city'].strip()
    except:
        pass
        
    try:
        postcode = addr['address']['postcode'].strip()
    except:
        pass
    
    try:
        county = addr['address']['county'].strip()
    except:
        pass
        
    try:    
        state = addr['address']['state'].strip()
    except:
        pass
        
    try:
        country = addr['address']['country']
    except:
        pass
    
    if name == road:
        name = ""
        
        
    if country == "United States":
        country = ""
        
    ident = name+" "+house_number+" "+road+" "+city+" "+state+" "+postcode+" "+country
    ident = ident.replace(" ","_")
    ident = ident.replace("__","_")
    
    if ident[0] == "_":
        ident = ident[1:]
        
    if ident[len(ident)-1] == "_":
        ident = ident[:-1]
        
    return ident
        
    



def sort_pic_or_doc_or_mov(sort_from_path, sort_to_path, sort_type):

    files_processed = 0
    items_processed = 0
    items_sorted = 0
    
    if sort_type == "pictures":
        mysorted = sort_to_path + "/sorted_pictures"
    elif sort_type == "documents":
        mysorted = sort_to_path + "/sorted_documents"
    elif sort_type == "movies":
        mysorted = sort_to_path + "/sorted_movies"
    elif sort_type == "backups":
        mysorted = sort_to_path + "/sorted_backups"
    else:
        print ("error")
        exit (0)
    
    isExist = os.path.exists(mysorted)
    if not isExist:
        print ("does not exist")
        os.mkdir(mysorted) 
        print ("sorted "+mysorted+" directory created")
    else:
        print (mysorted, "already exists, so not creating a new one...")
        
    p = Path(sort_from_path)
    for i in p.glob('**/*'):
    
        files_processed = files_processed + 1
        print ("files_processed: "+str(i)[-4:] , files_processed)
        
        #print(i.name, get_date(i))
        if not os.path.isdir(i):
            ext = str(i)[-4:]
            #print ("extension", extension)
            if sort_type == "pictures":
                if ext == ".jpg" or ext == '.JPG' or ext == ".NEF":
                    new_filename = ""
                    if i != None:
                        try:
                            coordinates = (image_coordinates(str(i)))
                        except:
                            pass
                        if coordinates != "No Coordinates" and coordinates != "No EXIF":
                       
                            print ("=== Good coordinates ===")
                            print (coordinates)
                            lng = coordinates['geolocation_lng']
                            lat = coordinates['geolocation_lat']
                            imageTakenTime = coordinates['imageTakenTime']
                            imageTakenTime = imageTakenTime.replace(":","-")
                            imageTakenTime = imageTakenTime.replace(" ","-at-")
                            photo_location = long_lat_to_address(lng, lat)
                            new_filename = imageTakenTime + "_" + photo_location
                            print(new_filename)
                        
                    if process_file(i, mysorted, sort_type, new_filename):
                        items_sorted = items_sorted + 1
                    items_processed = items_processed + 1
            
            
            elif sort_type == "documents":
                if ext == ".doc" or ext == "docx" or ext == ".pdf" or ext == ".xls" or ext == "xlsx" or ext == "pptx" or ext == ".ppt" or ext == ".rtf" or ext == ".txt":
                    if process_file(i, mysorted, sort_type, ""):
                        items_sorted = items_sorted + 1
                    items_processed = items_processed + 1
                    
            elif sort_type == "movies":
                if ext == ".mov" or ext == ".MOV" or ext == ".mov" or ext == ".mp4" or ext == ".MP4" or ext == ".avi":
                    if process_file(i, mysorted, sort_type, ""):
                        items_sorted = items_sorted + 1
                    items_processed = items_processed + 1
                    
            elif sort_type == "backups":
                if ext == ".tar" or ext == ".TAR" or ext == ".zip" or ext == ".ZIP" or ".gz" in ext:
                    if process_file(i, mysorted, sort_type, ""):
                        items_sorted = items_sorted + 1
                    items_processed = items_processed + 1
            else:
                print ("error")
                exit(0)
    return files_processed, items_processed, items_sorted
    
    
#get_location("26.7674446, 81.109758")  

#long_lat_to_address("81.109758", "26.7674446") 
#exit(0)
                
'''
How to use:
This program will sort your pictures, or documents or movies.
It will do one of:
pictures
documents
movies

And must be told which one you want to sort.

In all cases = a directory is made of:

sorted_pictures
or 
sorted_documents
or
sorted_movies

And by default saved from the "to" path you give the program.

For example:
to = "/Users/jfall" will make (in picture sort mode)
/Users/jfall/sorted_pictures

And in sorted pictures will be folders like:
11/2011  12/2013 1/1999 and on and on.
In those dated folders are the pictures.

The Exif date from the picture is tried first.
Then if the Exif date is not found the date of the picture file from the operating system is used.

The folders are created dynamically depending on what pictures are found.
duplicates with the same name and dates are overwritten.

======

myfrom is a path to your pictures stash. It will recursively process all files in there. Pictures or not. NO files are changed.
Pictures are copied to new folders. The folders are named by the date found in the picture or if not found then the date of the file.

to: This is just your login directory and pictures, documents or movies are written there in sorted folders

sort_type: May be one of "pictures" or "documents" or "movies"
'''                
sort_from_folder_path = "/Users/jfall/my_sorted_pictures"
home = str(Path.home())

'''
sort_type is "pictures" or "documents" or "movies" or "backups"
'''
sort_type = "pictures"
#sort_type = "documents"
#sort_type = "movies"
#sort_type = "backups"
                 
files_processed, items_processed, items_sorted = sort_pic_or_doc_or_mov(sort_from_folder_path, home, sort_type)                

print (" ")                    
print ("files processed: ",files_processed)           
      
print (sort_type+" processed: ",items_processed)
print (sort_type+" sorted:", items_sorted)
print ("possible duplicates in "+sort_from_folder_path+" are counted "+str(items_processed - items_sorted)+" and not copied to destination: ",home+"/sorted_"+sort_type)                
print ("DONE.")   
  