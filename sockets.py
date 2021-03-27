#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

myWorld = World()        

'''***************************************************************************'''
'''SRC: https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py '''
clients = list()

def send_all(msg):
    for client in clients:
        client.put( msg )

def send_all_json(obj):
    send_all( json.dumps(obj) )

class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, v):
        self.queue.put_nowait(v)

    def get(self):
        return self.queue.get()

'''***************************************************************************'''
def set_listener( entity, data ):
    ''' do something with the update ! '''
    new_entity = {entity: data}
    send_all_json(new_entity)

myWorld.add_set_listener( set_listener )
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    #return None
    return flask.redirect('static/index.html')

'''***************************************************************************'''
'''SRC: https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py '''
def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # XXX: TODO IMPLEMENT ME
    # return None
    try:
        while True:
            msg = ws.receive()
            print("WS RECV: %s" % msg)
            if (msg is not None):
                packet = json.loads(msg) 
                for key in packet:
                    myWorld.set(key, packet[key])
            else:
                break
    except:
        print("Done")

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # XXX: TODO IMPLEMENT ME
    # return None
    client = Client()
    clients.append(client)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print("WS Error %s" % e)
    finally:
        clients.remove(client)
        gevent.kill(g)

'''***************************************************************************'''


# I give this to you, this is how you get the raw body/data portion of a post in flask
# this should come with flask but whatever, it's not my project.
def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data.decode("utf8") != u''):
        return json.loads(request.data.decode("utf8"))
    else:
        return json.loads(request.form.keys()[0])

'''***************************************************************************'''
'''SRC: https://github.com/leah-is-offline/CMPUT404-assignment-ajax/blob/master/server.py '''
@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    #return None
    raw_post_data = flask_post_json()
    if request.method == "POST":
        myWorld.set(entity, raw_post_data)
    if request.method == "PUT":
        for key in raw_post_data:
            myWorld.update(entity,key,raw_post_data[key]) #dont return the world - should work for post as well?
    response = json.dumps(raw_post_data)
    status_code = 200
    return response, status_code


@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    #return None
    response = json.dumps(myWorld.world()) #RETURN THE WHOLE WORLD
    status_code = 200
    return response, status_code

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    #return None
    world_entity = myWorld.get(entity)
    response = json.dumps(world_entity)
    status_code = 200
    return response, status_code

@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    #return None
    myWorld.clear()
    response = json.dumps(myWorld.world()) 
    status_code = 200
    return response,status_code 
'''***************************************************************************'''


if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
