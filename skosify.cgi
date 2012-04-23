#!/usr/bin/env python

import cgi
import cgitb; cgitb.enable()
import sys
import tempfile
import os, os.path
import shutil
import time
import subprocess


# created temporary directory names include this prefix
TEMPDIR_PREFIX = 'skosify-cgi'
LOGFILE = "log.txt"

# maximum input file size, in kilobytes
MAX_FILE_SIZE = 5120

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
h2 { font-size: 1em }
#body {
  min-height: 20em;
  padding: 1em 1em;
}
h3 {
  display: inline;
  font-size: 1em;
  font-weight: bold;
  margin-right: 0.5em;
}
form {
  padding: 1em 1em;
  margin-top: 1em;
  margin-left: auto;
  margin-right: auto;
  max-width: 25em;
  background-color: #eeeeee;
}
.buttons {
  margin-top: 1em;
}
.warnings li {
  color: #800000;
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
"""

HEADER = """
<div id="header">
<h1>Skosify</h1>
<p id="tagline">validate and improve SKOS vocabularies</p>
</div>
"""

FOOTER = """
<div id="footer">&copy; Semantic Computing Research Group. <a href="http://www.seco.tkk.fi/tools/skosify">About Skosify</a></div>
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

getStatus = function() {
  var xhr = new XMLHttpRequest();
  xhr.open("GET", "status", true);
  xhr.onreadystatechange = function (ev) {
    if (xhr.readyState == 4) {
      if (xhr.status == 200) {
        var statusDiv = document.getElementById("status");
        statusDiv.innerHTML = "";
        data = eval("(" + xhr.responseText + ")");
        statusDiv.innerHTML = "<h2>Status: " + data["status"] + "</h2>";
        var html = "<ul id='phases'>";
        for (var i = 0; i < data["statuslines"].length; ++i) {
          var phase = data["statuslines"][i];
          html += "<li><h3>" + phase["name"] + "</h3>" + phase["description"] + "</li>";
          if (phase["warnings"].length > 0) {
            html += "<ul class='warnings'>";
            for (var j = 0; j < phase["warnings"].length; ++j) {
              var warning = phase["warnings"][j];
              html += "<li>" + warning + "</li>";
            }
            html += "</ul>";
          }
        }
        html += "</ul>";
        statusDiv.innerHTML += html;
        if (data["status"] == "error") {
          html  = "<h2 class='error'>Error</h2>";
          html += "<p class='error'>" + data["error"] + "</p>";
          statusDiv.innerHTML += html;
        }
        if (data["status"] == "finished") {
          html  = "<h2>Results</h2>";
          html += "<ul>";
          html += "<li><a href='" + data["output"] + "'>Processed vocabulary</a></li>";
          html += "<li><a href='" + data["report"] + "'>Full report</a></li>";
          html += "</ul>";
          statusDiv.innerHTML += html;
        } else if (data["status"] != "error") {
          setTimeout(getStatus, 1000);
        }
      } else {
        console.log("Error", xhr.statusText);
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



# function to print an error message & code and exit
def error(code, message):
  print "Content-Type: text/plain"
  print "Status:", code
  print
  print code, message
  sys.exit()


def front_page():
  print "Content-Type: text/html\n"
  print FRONT_PAGE
  sys.exit()

def process_form(input):
  if not input.filename:
    error(400, "No file given")

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
    if not chunk: break
    inputfile.write(chunk)
    i += 1
  inputfile.close()

  if i >= MAX_FILE_SIZE:
    shutil.rmtree(tempdir)
    error(400, "Maximum input file size %d KB exceeded" % MAX_FILE_SIZE)

  # use the random part of the tempdir name as session id
  session = os.path.basename(tempdir).replace(TEMPDIR_PREFIX, '')

  # determine where to find the skosify.py script, to be invoked by batch
  cgiscript = sys.argv[0]
  linktarget = os.readlink(cgiscript)
  if linktarget.startswith('/'): # absolute already
    abslinktarget = linktarget
  else:
    abslinktarget = os.path.abspath(os.path.join(os.path.dirname(cgiscript), linktarget))
  
  skosifyscript = os.path.join(os.path.dirname(abslinktarget), "skosify.py")

  print "Status: 303"
  print "Location:", os.environ['SCRIPT_NAME'] + "/" + session + "/"
  print # end of CGI headers
  
  stdout = os.path.join(tempdir, "stdout")
  stderr = os.path.join(tempdir, "stderr")

  # start a background process
  cmd = "%s --debug --output %s --log %s %s >%s 2>%s" % \
    (skosifyscript, outputfn, logfn, inputfn, stdout, stderr)
  batch = subprocess.Popen("batch", stdin=subprocess.PIPE)
  batch.communicate(input=cmd)
  

def start_session(session):
  print "Content-Type: text/html\n"
  print STATUS_PAGE
  sys.exit()


def return_status(session):
  statuslines = []
  status = "processing"
  error = None
  output = None
  report = os.environ['SCRIPT_NAME'] + "/" + session + "/report"
  
  tempdir = os.path.join(tempfile.gettempdir(), TEMPDIR_PREFIX + session)
  logfn = os.path.join(tempdir, LOGFILE)
  try:
    log = open(logfn, "r")
  except IOError:
    status = "starting"
    log = None

  if log:
    warnings = []
    for line in log:
      line = line.strip()
      if line.startswith('DEBUG: Phase'):
        if len(statuslines) > 0:
          statuslines[-1]['warnings'] = warnings
          warnings = []
        phasename, phasedesc = line.replace('DEBUG: ', '').split(': ')
        statuslines.append({'name': phasename, 'description': phasedesc, 'warnings': []})
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

  if len(statuslines) > 0:
    statuslines[-1]['warnings'] = warnings
  ret = {'statuslines': statuslines, 'status': status, 'error': error,
         'output': output, 'report': report}

  import json
  print "Content-Type: application/json\n"
  print json.dumps(ret)
  sys.exit()  

def return_output(session, filename):
  if filename.endswith('.rdf'):
    print "Content-Type: application/rdf+xml\n"
  elif filename.endswith('.ttl'):
    print "Content-Type: text/turtle\n"
  elif filename.endswith('.nt'):
    print "Content-Type: text/plain\n"
  else: 
    print "Content-Type: text/plain\n"
  # TODO n3 mime type?

  tempdir = os.path.join(tempfile.gettempdir(), TEMPDIR_PREFIX + session)
  outputfn = os.path.join(tempdir, filename)
  print open(outputfn, "r").read()
  sys.exit()

def return_report(session):
  print "Content-Type: text/plain\n"
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
  input = form['input']
  process_form(input)

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
  error(404, "Not Found") 
