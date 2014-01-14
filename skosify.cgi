#!/usr/bin/env python

import cgi
import cgitb
cgitb.enable()
import sys
import tempfile
import os
import os.path
import shutil
import time
import subprocess


# created temporary directory names include this prefix
TEMPDIR_PREFIX = 'skosify-cgi'
LOGFILE = "log.txt"

# maximum input file size, in kilobytes
MAX_FILE_SIZE = 5120  # default
# allow overriding value using environment variable
if 'SKOSIFY_MAX_FILE_SIZE' in os.environ:
    MAX_FILE_SIZE = int(os.environ['SKOSIFY_MAX_FILE_SIZE'])

STYLESHEET = """
<style type="text/css">
body {
  margin: 0;
  font-family: sans-serif;
}
#header {
  padding: 1em 1em;
  background-color: #3366cc;
  color: #ffffff;
}
#header h1, #header p {
  display: inline;
}
h1 {
  font-size: 1.3em;
  margin: 0 1em 0 0;
  color: #ffffff;
}
h2 { font-size: 1.2em }
#body {
  min-height: 20em;
  padding: 1em 1em;
}
div.phase {
  margin-top: 0.5em;
}
.done {
  color: #666666;
}
.phase h3 {
  display: inline;
  font-size: 1em;
  font-weight: bold;
  margin: 0 0.5em 0 0;
}
.phase p {
  display: inline;
  margin: 0 0 0 0;
}
.phase h4 {
  margin: 0 0 0 2em;
}
.phase ul {
  margin: 0 0 0 4em;
  padding: 0;
}
form {
  padding: 1em 1em;
  margin-left: auto;
  margin-right: auto;
  max-width: 32em;
  background-color: #eeeeee;
}
form p {
  margin: 0 0 0.5em 0;
  font-weight: bold;
  font-size: small;
}
fieldset {
  margin-top: 1em;
  border: 1px solid #dddddd;
  background-color: #f7f7f7;
}
.buttons {
  margin-top: 1em;
}
.warnings {
  color: #800000;
}
.infos {
  color: #603333;
}
.error {
  color: #cc0000;
}
#footer {
  background-color: #ddddff;
  text-align: center;
  font-size: small;
  padding: 0.2em;
}
#footer a {
  color: #3333ff;
}

</style>
<style id="hidewarnings">
.warnings .more { display: none; }
</style>
<style id="hideinfos">
.infos .more { display: none; }
</style>
"""

HEADER = """
<div id="header">
<h1>Skosify</h1>
<p id="tagline">validate and improve SKOS vocabularies</p>
</div>
"""

FOOTER = """
<div id="footer">&copy; Semantic Computing Research Group.
<a href="http://www.seco.tkk.fi/tools/skosify">About Skosify</a></div>
"""

FRONT_PAGE = """<!DOCTYPE html>
<html>
<head>
<title>Skosify</title>
%s
</head>
<body>
%s
<div id="body">
<form action="" method="POST" enctype="multipart/form-data">
<p id="help">Select a SKOS file to upload (maximum size: %d KB)</p>

<div class="field">
<label for="input">Input file:</label>
<input type="file" name="input" />
</div>

<fieldset>
<legend>Validity options</legend>
<div class="field">
<input type="checkbox" name="keep-related" value="1" />
<label for="keep-related">
  Keep skos:related relationships within the same hierarchy
</label>
</div>
<div class="field">
<input type="checkbox" name="break-cycles" value="1" />
<label for="keep-related">
  Break any cycles in the skos:broader hierarchy
</label>
</div>
</fieldset>

<fieldset>
<legend>Output options</legend>
<div class="field">
<input type="checkbox" name="narrower" value="1" checked="checked" />
<label for="narrower">Include skos:narrower relations in output</label>
</div>
<div class="field">
<input type="checkbox" name="transitive" value="1" />
<label for="transitive">
  Include transitive hierarchical relations in output
</label>
</div>
</fieldset>

<div class="buttons">
<input type="submit" name="submit" value="Process" />
</div>

</form>
</div>
%s
</body>
</html>
""" % (STYLESHEET, HEADER, MAX_FILE_SIZE, FOOTER)

STATUS_SCRIPT = """
<script type="text/javascript">

function toggleWarnings() {
  var style = document.getElementById("hidewarnings");
  style.disabled = !style.disabled;
  return false;
}

function toggleInfos() {
  var style = document.getElementById("hideinfos");
  style.disabled = !style.disabled;
  return false;
}

function getStatus() {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "status", true);
  xhr.onreadystatechange = function (ev) {
    if (xhr.readyState == 4) {
      if (xhr.status == 200) {
        var statusDiv = document.getElementById("status");
        data = eval("(" + xhr.responseText + ")");
        statusDiv.innerHTML = "<h2>Status: " + data["status"] + "</h2>";
        var html = "";
        for (var i = 0; i < data["phases"].length; ++i) {
          var phase = data["phases"][i];
          if (data["status"] == "processing" && data["phases"].length == i+1) {
            var phasestatus = "current";
          } else {
            var phasestatus = "done";
          }
          html += "<div class='phase " + phasestatus + "'>";
          html += "<h3>" + phase["name"] + "</h3>" \
                  + "<p>" + phase["description"] + "</p>";
          if (phase["warnings"].length > 0) {
            var warnings = phase["warnings"];
            html += "<h4 class='warnings'>Warnings (" + warnings.length + ")";
            if (phase["warnings"].length > 3) {
              html += " <a href='#' onclick='return toggleWarnings();'>" +
                      "show / hide full list</a>";
            }
            html += "</h4>";
            html += "<ul class='warnings'>";
            for (var j = 0; j < warnings.length; ++j) {
              var cl = (j > 2) ? 'more' : '';
              html += "<li class='" + cl + "'>" + warnings[j] + "</li>";
            }
            html += "</ul>";
          }
          if (phase["infos"].length > 0) {
            var infos = phase["infos"]
            html += "<h4 class='infos'>Messages (" + infos.length + ")";
            if (phase["infos"].length > 3) {
              html += " <a href='#' onclick='return toggleInfos();'>" +
                      "show / hide full list</a>";
            }
            html += "</h4>";
            html += "<ul class='infos'>";
            for (var j = 0; j < infos.length; ++j) {
              var cl = (j > 2) ? 'more' : '';
              html += "<li class='" + cl + "'>" + infos[j] + "</li>";
            }
            html += "</ul>";
          }
          html += "</div>";
        }
        statusDiv.innerHTML += html;
        if (data["status"] == "error") {
          html  = "<h2 class='error'>Error</h2>";
          html += "<p class='error'>" + data["error"] + "</p>";
          statusDiv.innerHTML += html;
        }
        if (data["status"] == "finished") {
          html  = "<h2>Results</h2>";
          html += "<ul>";
          html += "<li><a href='" + data["output"] + "'>" +
                  "Processed vocabulary</a></li>";
          html += "<li><a href='" + data["report"] + "'>" +
                  "Full report</a></li>";
          html += "</ul>";
          statusDiv.innerHTML += html;
        } else if (data["status"] != "error") {
          setTimeout(getStatus, 1000);
        }
      } else {
        var statusDiv = document.getElementById("status");
        statusDiv.innerHTML = "Backend error: " + xhr.statusText;
      }
    }
  };
  xhr.send(null);
};
getStatus();

</script>
"""

STATUS_PAGE = """<!DOCTYPE html>
<html>
<head>
<title>Skosify - processing</title>
%s
%s
</head>
<body>
%s
<div id="body">
<div id="status">
</div>
</div>
%s
</body>
</html>
""" % (STYLESHEET, STATUS_SCRIPT, HEADER, FOOTER)

# function to start HTTP headers


def start_http(mimetype=None, headers={}):
    if mimetype:
        print "Content-Type: %s" % mimetype
    for name, value in headers.items():
        print "%s: %s" % (name, value)
    print "Cache-Control: no-cache, no-store, max-age=0"
    print  # end of headers

# function to print an error message & code and exit


def return_error(code, message):
    start_http("text/plain", {"Status": code})
    print code, message
    sys.exit()


def front_page():
    start_http("text/html")
    print FRONT_PAGE
    sys.exit()


def process_form(form):
    input = form['input']
    if not input.filename:
        return_error(400, "No file given")

    # determine original file extension, which can be used to detect format
    ext = ""
    if '.' in input.filename:
        ext = "." + input.filename.split('.')[-1].lower()
    # make sure it's a known file extension, otherwise ignore it
    if ext not in [".rdf", ".owl", ".ttl", ".n3", ".nt"]:
        ext = ""

    # store the input as a temporary file
    tempdir = tempfile.mkdtemp(prefix=TEMPDIR_PREFIX)
    logfn = os.path.join(tempdir, "log.txt")
    logfn = os.path.join(tempdir, "log.txt")
    outputfn = os.path.join(tempdir, "output" + ext)
    inputfn = os.path.join(tempdir, "input" + ext)
    inputfile = open(inputfn, "wb")

    i = 0
    while i < MAX_FILE_SIZE:
        chunk = input.file.read(1024)
        if not chunk:
            break
        inputfile.write(chunk)
        i += 1
    inputfile.close()

    if i >= MAX_FILE_SIZE:
        shutil.rmtree(tempdir)
        return_error(400, "Maximum input file size %d KB exceeded" %
                     MAX_FILE_SIZE)

    # use the random part of the tempdir name as session id
    session = os.path.basename(tempdir).replace(TEMPDIR_PREFIX, '')

    # determine where to find the skosify.py script, to be invoked by at
    if 'SKOSIFY_PATH' in os.environ:
        # path explicitly set by environment variable, so use the setting
        skosifyscript = os.environ['SKOSIFY_PATH']
    else:
        # not set, so determine the location by following CGI symlink
        cgiscript = sys.argv[0]
        linktarget = os.readlink(cgiscript)
        if linktarget.startswith('/'):  # absolute already
            abslinktarget = linktarget
        else:
            abslinktarget = os.path.abspath(
                os.path.join(os.path.dirname(cgiscript), linktarget))
        skosifyscript = os.path.join(
            os.path.dirname(abslinktarget), "skosify.py")

    stdout = os.path.join(tempdir, "stdout")
    stderr = os.path.join(tempdir, "stderr")

    # determine options
    options = []
    if form.getfirst("narrower"):
        options.append('--narrower')
    else:
        options.append('--no-narrower')
    if form.getfirst("transitive"):
        options.append('--transitive')
    else:
        options.append('--no-transitive')
    if form.getfirst("keep-related"):
        options.append('--keep-related')
    else:
        options.append('--no-keep-related')
    if form.getfirst("break-cycles"):
        options.append('--break-cycles')
    else:
        options.append('--no-break-cycles')
    options = ' '.join(options)

    # start a background skosify process
    cmd = "%s %s --debug --output %s --log %s %s >%s 2>%s" % \
        (skosifyscript, options, outputfn, logfn, inputfn, stdout, stderr)
    at = subprocess.Popen(["at", "now"], stdin=subprocess.PIPE)
    at.communicate(input=cmd)

    # clean up the temporary directory tomorrow (i.e. after 24 hours)
    cmd = "rm -rf %s" % tempdir
    at = subprocess.Popen(["at", "tomorrow"], stdin=subprocess.PIPE)
    at.communicate(input=cmd)

    loc = os.environ['SCRIPT_NAME'] + "/" + session + "/"
    start_http(headers={"Status": "303", "Location": loc})
    sys.exit()


def start_session(session):
    tempdir = os.path.join(tempfile.gettempdir(), TEMPDIR_PREFIX + session)
    if not os.path.exists(tempdir):
        return_error(404, "Not Found")

    start_http("text/html")
    print STATUS_PAGE
    sys.exit()


def return_status(session):
    phases = []
    status = "processing"
    error = None
    output = None
    report = os.environ['SCRIPT_NAME'] + "/" + session + "/report"

    tempdir = os.path.join(tempfile.gettempdir(), TEMPDIR_PREFIX + session)
    if not os.path.exists(tempdir):
        return_error(404, "Not Found")
    logfn = os.path.join(tempdir, LOGFILE)
    try:
        log = open(logfn, "r")
    except IOError:
        status = "starting"
        log = None

    if log:
        warnings = []
        infos = []
        for line in log:
            line = line.strip()
            if line.startswith('DEBUG: Phase'):
                if len(phases) > 0:
                    phases[-1]['warnings'] = warnings
                    phases[-1]['infos'] = infos
                    warnings = []
                    infos = []
                phasename, phasedesc = line.replace('DEBUG: ', '').split(': ')
                phases.append(
                    {'name': phasename,
                     'description': phasedesc,
                     'warnings': []})
            elif line.startswith('DEBUG: Writing'):
                fn = os.path.basename(line.split()[4])
                output = os.environ['SCRIPT_NAME'] + "/" + session + "/" + fn
            elif line.startswith('CRITICAL: '):
                status = "error"
                error = line.replace('CRITICAL: ', '').strip()
            elif line.startswith('DEBUG: Finished'):
                status = "finished"
            elif line.startswith('WARNING: '):
                warnings.append(line.replace('WARNING: ', ''))
            elif line.startswith('INFO: '):
                infos.append(line.replace('INFO: ', ''))

    if len(phases) > 0:
        phases[-1]['warnings'] = warnings
        phases[-1]['infos'] = infos
    ret = {'phases': phases, 'status': status, 'error': error,
           'output': output, 'report': report}

    import json
    start_http("application/json")
    print json.dumps(ret)
    sys.exit()


def return_output(session, filename):
    if filename.endswith('.rdf'):
        start_http("application/rdf+xml")
    elif filename.endswith('.ttl'):
        start_http("text/turtle")
    elif filename.endswith('.nt'):
        start_http("text/plain")
    elif filename.endswith('.n3'):
        start_http("text/n3")
    else:  # default is RDF/XML
        start_http("application/rdf+xml")

    tempdir = os.path.join(tempfile.gettempdir(), TEMPDIR_PREFIX + session)
    outputfn = os.path.join(tempdir, filename)
    print open(outputfn, "r").read()
    sys.exit()


def return_report(session):
    start_http("text/plain; charset=UTF-8")
    tempdir = os.path.join(tempfile.gettempdir(), TEMPDIR_PREFIX + session)
    logfn = os.path.join(tempdir, LOGFILE)
    print open(logfn, "r").read()
    sys.exit()


# Determine what to do, based on PATH_INFO and/or form submission
path = os.environ.get('PATH_INFO', None)
form = cgi.FieldStorage()

# Front page
if not path and 'input' not in form:
    front_page()

# Handle input form (file upload + parameters) and start processing
if not path and 'input' in form:
    process_form(form)

elif path:
    parts = path.split('/')
    session = parts[1]
    method = parts[2]
    if not method:
        start_session(session)
    elif method == "status":
        return_status(session)
    elif method.startswith('output'):
        return_output(session, method)
    elif method.startswith('report'):
        return_report(session)
else:
    return_error(404, "Not Found")
