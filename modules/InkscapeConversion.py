__author__ = 'wolverine'


import subprocess
import os.path

def convertSvgEmf(inkscapeExecutable, filename):
    basename, ext = os.path.splitext(filename)
    emfname = basename + ".emf"
    subprocess.call([inkscapeExecutable, filename, "--export-emf={0}".format(emfname)])

def convertSvgPdf(inkscapeExecutable, filename):
    basename, ext = os.path.splitext(filename)
    pdfname = basename + ".pdf"
    subprocess.call([inkscapeExecutable, filename, "--export-pdf={0}".format(pdfname)])