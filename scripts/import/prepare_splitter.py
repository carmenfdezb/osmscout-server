#!/usr/bin/env python2.7

import os, collections, json

base_dir = os.path.abspath("hierarchy")

planet = "planet/planet-latest.osm.pbf"
splitted_dir = os.path.abspath("splitted")
helper_dir = os.path.abspath("splitted/helper")
configs_dir = os.path.abspath("splitted/configs")

#####################################################

def ignore(d):
    return os.path.exists(d + "/ignore")

def get_from_parent(d, fname):
    dirs = d.split("/")
    base = base_dir.split("/")
    i = len(dirs)-1
    while i > len(base):
        k = ""
        if d[0] == "/": k = "/"
        for j in range(i): k = os.path.join(k, dirs[j])
        k = os.path.join(k, fname)
        if os.path.exists(k):
            return k
        i -= 1
    return None

def get_base_name(d):
    base_list = base_dir.split("/")
    rlist = d.split("/")
    ri = len(base_list)
    target = rlist[ri]
    ri+=1
    while ri < len(rlist):
        target += "-" + rlist[ri]
        ri += 1
    return target

def prepared(name):
    if name == planet: return ""
    return "$(HELP_DIR)/" + name + ".prepared"

def processed(name):
    if name == planet: return "$(HELP_DIR)/planet.processed"
    return "$(HELP_DIR)/" + name + ".processed"

def pbf(name):
    if name == planet: return name
    return splitted_dir + "/" + name + ".pbf"

#####################################################
## MAIN

Depends = collections.defaultdict(list)

for root, folders, files in os.walk(base_dir):
    if "poly" in files:
        parent = get_from_parent(root, "poly")
        if parent is None:
            parent = planet
        else:
            parent = get_base_name(os.path.dirname(parent))

        target = get_base_name(root)

        poly = os.path.join(root, "poly")
        Depends[ parent ].append({ "target": target, "poly": poly })

fmake = open("Makefile.splitter", "w")

fmake.write("""
# This Makefile is generated by script prepare_splitter.py

HELP_DIR=%s

""" % (helper_dir))

fmake.write("""
all: %s/.directory $(HELP_DIR)/.directory $(HELP_DIR)/all_done
	echo All done

%s/.directory:
	mkdir -p %s
	touch %s/.directory

$(HELP_DIR)/.directory:
	mkdir -p $(HELP_DIR)
	touch $(HELP_DIR)/.directory

OSMIUM=osmium/install/bin/osmium

""" % (splitted_dir, splitted_dir, splitted_dir, splitted_dir) )

if not os.path.exists(configs_dir):
    os.makedirs(configs_dir)

config_count = 0
all_pbfs = []
for k in Depends:
    for j in Depends[k]:
        all_pbfs.append(j["target"])

        fmake.write(prepared(j["target"]) + ": $(HELP_DIR)/.directory " + processed(k) +
                    "\n\ttouch " + prepared(j["target"]) + "\n\n")

    fmake.write(processed(k) + ": $(HELP_DIR)/.directory " + prepared(k) + " ")
    for j in Depends[k]: fmake.write(" " + j["poly"])
    if k == planet: fmake.write(" " + planet)

    extracts = []
    for j in Depends[k]:
        extracts.append( { "output":  pbf(j["target"]),
                           "output_format": "pbf",
                           "polygon": {
                               "file_name": j["poly"],
                               "file_type": "poly"
                               }
                           } )
    cname = os.path.join(configs_dir, str(config_count))
    config_count += 1
    with open(cname, "w") as f:
        f.write( json.dumps( { "extracts": extracts }, sort_keys=True, indent=4, separators=(',', ': ') ) )
    
    fmake.write("\n\t$(OSMIUM) extract -c " + cname + " --overwrite -s smart " + pbf(k))
    fmake.write("\n\ttouch " + processed(k) + "\n\n")

fmake.write("\n$(HELP_DIR)/all_done:")
for i in all_pbfs:
    fmake.write(" " + prepared(i))
fmake.write("\n\ttouch $(HELP_DIR)/all_done\n")

