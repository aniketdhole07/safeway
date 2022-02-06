

from app import app
from flask import render_template, request, redirect, url_for
import numpy as np
import pandas as pd
import folium
from folium.plugins import HeatMap
from folium import CircleMarker
import tweepy
from geopy.geocoders import Nominatim


donation_list=[]
incident_list=[]
###
# Routing for your application.
###
hmap=None
geolocator = Nominatim(user_agent="Your_Name")

@app.route('/')
def home():
    global hmap
    """Render website's home page."""
    df = pd.read_csv('/data/past_location.csv')
    max_amount = float(df['KY_CD'].max())
    if(not(hmap)):
        hmap = folium.Map(location=[40.8, -73.7], zoom_start=10, )
        hm_wide = HeatMap( list(zip(df.Latitude.values, df.Longitude.values, df.KY_CD.values.astype(float))),
                        min_opacity=0.2,
                        max_val=max_amount,
                        radius=17, blur=15, 
                        max_zoom=1, 
                        )
        hmap.add_child(hm_wide)
    for i in donation_list:
       hm_wide = CircleMarker(location=[i[0], i[1]],radius=3,weight=5,color = 'green',popup=i[2]) 
       hmap.add_child(hm_wide)
    hmap.save('/app/templates/map.html')
    return render_template('home.html')

@app.route('/map')
def map():
    return render_template('map.html')

def checker(x1,y1,r,x2,y2):
    if ((x2 - x1) * (x2 - x1) +
        (y2 - y1) * (y2 - y1) <= r * r):
        return True
    else:
        return False

@app.route('/live_data', methods=['GET', 'POST'])
def handle_data():
    global geolocater
    user_location = request.form['Enter Address']
    client = tweepy.Client(bearer_token='ENTER Your Twitter Bearer Token')
    query = 'from:nyc_alerts911'
    tweets = client.search_recent_tweets(query=query, tweet_fields=['context_annotations', 'created_at'], max_results=30)
    
    location = geolocator.geocode(user_location)
    la1,lo1=location.latitude, location.longitude
    safe_col='green'
    hmap1 = folium.Map(location=[la1,lo1], zoom_start=11, )
    recent_points={}
    recent_points["lat"]=[]
    recent_points["lon"]=[]
    recent_points["val"]=[]
    recent_points["loc"]=[]
    for tweet in tweets.data:
        try:
            l1,l2=str(tweet).split("\n")
            location = geolocator.geocode(l1)
            lat,lon=location.latitude, location.longitude
            recent_points["lat"].append(lat)
            recent_points["lon"].append(lon)
            recent_points["val"].append(l2)
            recent_points["loc"].append(l1)
        except:
            print("[SORTED] API DATA")
    
    tmp=list(zip(recent_points["lat"], recent_points["lon"], recent_points["val"], recent_points["loc"]))
    tmp2=[]
    for i1 in range(len(recent_points["loc"])):
        tmp2.append([recent_points["loc"][i1],recent_points["val"][i1]])
    for i1 in range(len(incident_list)):
        tmp2.append([incident_list[i1][4],incident_list[i1][5]])
    for i in tmp:
        hm_wide = CircleMarker(location=[i[0], i[1]],radius=2,weight=5,color = 'black',popup=i[2])
        if(checker(float(la1),float(lo1),1609.344/57.29,float(i[0]),float(i[1]))):
            safe_col="red"
        hmap1.add_child(hm_wide)
    for i in incident_list:
        hm_wide = CircleMarker(location=[i[0], i[1]],radius=2,weight=5,color = 'brown',popup=i[2])
        if(checker(float(la1),float(lo1),1609.344/57.29,float(i[0]),float(i[1]))):
            safe_col="red"
        hmap1.add_child(hm_wide)
    folium.Circle(location=[la1,lo1],
              radius=1000,
              fill_color=safe_col,
              fill_opacity = 0.5
              ).add_to(hmap1)
    data="You are in DANGER zone please safetly evacuate your area"
    hmap1.save('/app/templates/map.html')
    return render_template('live_data.html',data=data,data1=tmp2)

@app.route('/unsafe', methods=['GET', 'POST'])
def unsafe():
    message = ''
    if request.method == 'POST':
        name = request.form.get('name')  # access the data inside 
        locat = request.form.get('location')
        details  = request.form.get('item')
        location = geolocator.geocode(locat)
        lat2,lon2=location.latitude, location.longitude
        message="Submitted Request Successfully"
        incident_list.append([lat2,lon2,"By : "+str(name)+"\n"+str(details),name,locat,details])
    return render_template('unsafe.html', message=message)

@app.route('/donations', methods=['GET', 'POST'])
def donation(): 
    message = ''
    if request.method == 'POST':
        name = request.form.get('name')  # access the data inside 
        locat = request.form.get('location')
        details  = request.form.get('item')
        location = geolocator.geocode(locat)
        lat2,lon2=location.latitude, location.longitude
        message="Submitted Request Successfully"
        donation_list.append([lat2,lon2,"By : "+str(name)+"\n"+str(details),name,locat,details])
    return render_template('donation.html', message=message)

@app.route('/donationmap', methods=['GET', 'POST'])
def donationmap():
    hmap2 = folium.Map(location=[40.8, -73.7], zoom_start=10, )
    for i in donation_list:
       hm_wide = CircleMarker(location=[i[0], i[1]],radius=3,weight=5,color = 'green',popup=i[2]) 
       hmap2.add_child(hm_wide)
    hmap2.save('/home/aniket/Desktop/Projects/flask_crime/app/templates/map.html')
    return render_template('donationmap.html', data=donation_list)

@app.route('/about/')
def about():
    """Render the website's about page."""
    return render_template('about.html', name="SafeWay")


def flash_errors(form):
    for field, errors in form.errors.items():
        for error in errors:
            flash(u"Error in the %s field - %s" % (
                getattr(form, field).label.text,
                error
            ), 'danger')

@app.route('/<file_name>.txt')
def send_text_file(file_name):
    """Send your static text file."""
    file_dot_text = file_name + '.txt'
    return app.send_static_file(file_dot_text)


@app.after_request
def add_header(response):
    """
    Add headers to both force latest IE rendering engine or Chrome Frame,
    and also tell the browser not to cache the rendered page. If we wanted
    to we could change max-age to 600 seconds which would be 10 minutes.
    """
    response.headers['X-UA-Compatible'] = 'IE=Edge,chrome=1'
    response.headers['Cache-Control'] = 'public, max-age=0'
    return response


@app.errorhandler(404)
def page_not_found(error):
    """Custom 404 page."""
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.run(debug=True,host="0.0.0.0",port="8080")
