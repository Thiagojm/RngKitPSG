from string import Template


class MyTemplate(Template):
    delimiter = '&'

# Change parameters
appname = "RngKit"
compname = "Conscienciology"
descript = "This application uses two types of TRNGs - True Random Number Generators (TrueRNG and Bitbbabler) for data collection and statistical analysis for several purposes, including mind-matter interaction research."
vmajor = 2
vminor = 1
vbuild = 5
helpurl = ""
updateurl = ""
abouturl = ""
installsize = 71275
iconpath = "src/images/BitB.ico"
builder = "py"

# ---------------------------------------------------------------#


outfile = f'{appname.replace(" ", "")}-installer-{vmajor}{vminor}{vbuild}-{builder}.exe'
iconpathrev = iconpath.replace("/", '\\')
iconpathrev = f"\\{iconpathrev}"


d = {
    'appname': appname,
    'compname': compname,
    "descript": descript,
    "vmajor": vmajor,
    "vminor": vminor,
    "vbuild": vbuild,
    "helpurl": helpurl,
    "updateurl": updateurl,
    "abouturl": abouturl,
    "installsize": installsize,
    "iconpath": iconpath,
    "outfile": outfile,
    "iconpathrev": iconpathrev,
}

with open('nsis_template.txt', 'r') as f:
    src = MyTemplate(f.read())
    result = src.substitute(d)

with open(f'{appname}-installer-{vmajor}{vminor}{vbuild}.txt', 'w') as g:
    g.write(result)