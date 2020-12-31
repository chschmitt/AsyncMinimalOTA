import pathlib
import gzip
import string
import textwrap

header_template = '''#ifndef AsyncMinimalOTAPage_h
#define AsyncMinimalOTAPage_h

const uint32_t MINIMAL_HTML_SIZE = ${size};
const uint8_t MINIMAL_HTML[] PROGMEM = ${data};

#endif
'''


def format_data(data):
    formatted = ' '.join(str(v) for v in data)
    lines = textwrap.wrap(formatted, width=80)
    joined = ',\n'.join(line.replace(' ', ',') for line in  lines)
    return f'{{\n{joined}\n}}'


if __name__ == '__main__':
    template = string.Template(header_template)
    codebase = pathlib.Path(__file__).absolute().parent 
    source = codebase / 'ui' / 'page.html'
    data = gzip.compress(source.read_bytes(), mtime=0)
    content = template.substitute(size=len(data), data=format_data(data))
    target = codebase / 'src' / 'AsyncMinimalOTAPage.h'
    target.write_text(content, encoding='utf-8')
