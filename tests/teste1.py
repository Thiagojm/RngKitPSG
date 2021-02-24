from string import Template

d = {
    'title': 'This is the title',
    'subtitle': 'And this is the subtitle',
    'list': '\n'.join(['first', 'second', 'third'])
}

with open('nsis_template.txt', 'r') as f:
    src = Template(f.read())
    result = src.substitute(d)
    print(result)

with open('nsis_template.txt', 'w') as g:
    g.write(result)