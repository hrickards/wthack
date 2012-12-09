# INPUT id
# OUTPUT MAGIC SHIT WITH MRIs
# OpenCV

# INPUT obj
# OUTPUT gcode

import Levenshtein
import cherrypy
import json
import os
import convert_obj_three
import threading
import glob

parts = map(lambda r: r.split("\t"), open('parts_list.txt', 'r').read().split("\n")[1:-1])
parts = map(lambda r: {'bid': r[0], 'name': r[1]}, parts)

def slice_gcode(bid):
    try:
        gcode = open('output/%s.gcode' % bid)
        cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
        return gcode
    except IOError as e:
        print "slic3r.pl data/%s.obj -o output/%s.gcode" % (bid, bid)
        t = threading.Thread(target=lambda: os.system("slic3r.pl data/%s.obj -o output/%s.gcode" % (bid, bid)))
        t.start()
        return json.dumps({'status': 'Slicing. Try again soon'})

class API(object):
    def list_of_bones(self):
        existing_parts = filter(lambda r: os.path.isfile("data/%s.obj" % r['bid']), parts)
        return json.dumps(existing_parts)

    def id_to_render(self, bid):
        if bid == "bone":
            cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
            return open('bone.js')

        infile = "data/%s.obj" % bid
        outfile = "output/%s.js" % bid

        if not os.path.isfile(outfile): convert_obj_three.convert_ascii(infile, "", "", outfile)
        cherrypy.response.headers['Content-Type'] = 'text/javascript'
        return open(outfile, 'r').read()

    def name_to_id(self, name):
        part = sorted(parts, key=lambda r:Levenshtein.ratio(r['name'], str(name)))[-1]
        return json.dumps(part)

    def id_to_obj(self, bid):
        cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
        if bid.replace(".obj", "") == "bone": return open("bone.obj", "r").read()
        return open("data/%s" % bid, 'r').read()

    def id_to_gcode(self, raw_bid):
        bid = raw_bid.replace(".obj", "").replace(".stl", "").replace(".gcode", "")
        if bid == "bone":
            cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
            return open('bone.gcode')
        return slice_gcode(bid)

    def obj_to_gcode(self, obj):
        m = md5.new(obj)
        bid = m.digest()

        out_f = open("data/%s.obj" % bid, "wb")
        out_f.write(obj.file.read())
        out_f.close()

        return slice_gcode(bid)

    def ct_to_stl(self, *args):
        cherrypy.response.headers['Content-Type'] = 'application/octet-stream'
        return open('static/bone.stl')

    def all_data(self):
        data = map(lambda r: r.replace(".obj", "").replace("data/", ""), glob.glob("data/*.obj"))
        data = map(lambda r: {'id': r, 'name': filter(lambda s: s['bid'] == r, parts)[0]['name'], 'link': "/api/id_to_obj/%s.obj" % r }, data)
        response = data

        return json.dumps(response)



    name_to_id.exposed = True
    list_of_bones.exposed = True
    id_to_obj.exposed = True
    id_to_gcode.exposed = True
    obj_to_gcode.exposed = True
    id_to_render.exposed = True
    ct_to_stl.exposed = True
    all_data.exposed = True

class Root(object): pass
PATH = os.path.abspath(os.path.dirname(__file__))

cherrypy.config.update({'server.socket_port': 9999})
cherrypy.config.update({'server.socket_host': '0.0.0.0'})
cherrypy.tree.mount(API(), '/api')
cherrypy.tree.mount(Root(), '/', config={
    '/': {
        'tools.staticdir.on': True,
        'tools.staticdir.dir': "%s/static/" % PATH,
        'tools.staticdir.index': 'index.html',
        },
    })
cherrypy.engine.start()
cherrypy.engine.block()
