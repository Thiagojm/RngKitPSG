from string import Template


class MyTemplate(Template):
    delimiter = '&'

# Change parameters
appname = "testeapp"
compname = "testecomp"
descript = "bla bla bla"
vmajor = 2
vminor = 3
vbuild = 4
helpurl = "www.ae.com"
updateurl = "www.ae.com/seila"
abouturl = "www.ae.com/seila/mano"
installsize = 61234
iconpath = "/src/images/BitB.ico"

# ---------------------------------------------------------------#


outfile = f'{appname.replace(" ", "")}-installer-{vmajor}{vminor}{vbuild}.exe'
iconpathrev = iconpath.replace("/", '\\')


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