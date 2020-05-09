import re
import os
from typing import List, Dict, Optional, Tuple, Union

"""
Мануал:
Скопируйте все темплейты из Зопы в файлы с такими же названиями, как в зопе, и с расширениями .html. 
Скопируйте все скрипты из Зопы в файл расширениям .py. Каждый зоповский скрипт поместите в функцию с назавнием скрипта 
зопы. 
В полученном файле рекомендуется свернуть многострочные сигнатуры в одну строку, заменить смиволы, заменяющие пробелы
(если есть (бывает, но редко)) на собственно пробелы, а также выровнять отступы.

Скопируйте все sql запросы из Зопы в файлы с такими же названиями, как в зопе, и с расширениями .sql. 
Соберите все файлы в одну папку и залейте туда этот скрипт
ВНИМАНИЕ! Скрипт исправит содержимое файлов, так что лучше сделать бекап в другой папке.
Запустите его
Введите имя ИТСД по-программистски, чтобы скрипт мог вставить его в редеректы и вызовы шаблонизатора
...
PROFIT!!

Темплейты изменены на джинджаподобные!
Осталось допилить напильником структуру и проверить все глазками на наличие ошибок (я протестил на своем ИТСД, 
возможно в ваших есть особые случаи, которые я не встречал.)

Кроме того:
1) Скрипт не добавляет {% endfor %}. Пока не придумал как это правильно сделать
2) Предполагается, что у вас есть базовый темплейт, от которого будет наследоваться текущий, поэтому вверху всегда 
добавляется extends. Содержание шаблона помещается в блок content


Питоновский файл тоже преобразился:
1) к функциям добавлен декоратов @module.route. Ко всем, но везде это нужно, поэтому выпилите лишние.
2) Выпилена зоповская дичь, типа request=container.REQUEST и RESPONSE=request.RESPONSE. request заменен на фласковский
3) Соответственно, все обращения к реквесту сделаны через request.args.get()
4) Вызовы шаблонов типа container.template(...) заменены на render_template('{ITSD_name}/template.html, ...)
5) Запросы к базе из вида container.BD_PROC(...) заменяются на with module.database.acquire(True): 
    tr.execute(BD_PROC, ...) если в папке имеется файл с название BD_PROC.sql. Все (которые я встречал) запросы к бд в 
    зопе происходят через 'select * from BD_PROC(?)'. Вопросительные знаки подставляются этим скриптом по количеству 
    переменных. 
6) Часто встречаются запросы к базе прямо внутри конструкции for in. Такие вещи тоже заменены. 
    Было:
    for var in container.BD_PROC(...):
    Стало:
    with module.database.acquire(True): 
        for var in tr.execute(BD_PROC, ...)
7) RESPONSE.redirect('some_view?...') => redirect('/some_view/?...')

Проблемы:
1) После работы нужно, естественно проверить все глазами и поправить сбившуюся структуру. Осташиеся ссылки вида 
container.something(...), скорее всего, будут являться сслыками на вьюхи, но проверьте
2) Проверяйте SQL-запросы. Там могут быть случайно удалены пробелы 
3) В Иггдрассиль аргументы у ДАО БД-ответа называются в нижнем регистре, а в зопе - в верхнем. Скрипт переделывает 
большую часть, кроме обращений вида dao['VARIABLE'] и некоторых других. Перепиливаем руками в dao.variable

Инджой)
Вопросы и контрибьюты приветствуются

ПС: это говнокод, написанный мной на коленке. Автор и сам понимает ущербность написанного, так что нечего предъявлять)
"""


def tal_condition_handler(line: str) -> str:
    condition: List = re.findall("tal:condition=[',\"]([A-z0-9/|.'() _]+)[',\"]", line) or \
                      re.findall("tal:condition=\" ?python: ?([^\"]+)\"", line)
    if not condition:
        return line
    condition: str = condition[0]
    if 'container' in condition:
        content = re.findall("container\.(\w+)\(([A-z0-9='.() ,_]*)\)", condition)[0]
        variables, query = get_bd_request(content)
        if query:
            condition: str = re.sub(
                f"container\.\w+\([A-z0-9='.() ,_]*\)",
                f'module.database.acquire(True).execute("{query}", ({", ".join(variables)},))',
                condition
            )
    line = re.sub("tal:condition=[',\"]([A-z0-9/|.'() _]+)[',\"]", '', line)
    line = re.sub("tal:condition=\" ?python: ?([^\"]+)\"", '', line)
    line = "{% if " + condition + " %}" + line + "{% endif %}"
    return line


def tal_content_handler(line: str) -> str:
    line: str = re.sub("tal:content=[',\"]structure ([A-z0-9/|.'() _]+)[',\"]", r'/> {{ \1 | safe }}', line)
    contents: List[str] = re.findall("tal:content=[',\"]([A-z0-9/|.'() _]+)[',\"]", line) + \
                          re.findall("tal:content=\" ?python: ?([^\"]+)\"", line)
    if not contents:
        return line
    for content in contents:
        line = re.sub("tal:content=[',\"]([A-z0-9/|.'() _]+)[',\"]", '', line)
        line = re.sub("tal:content=\" ?python: ?([^\"]+)\"", '', line)
        line = re.sub("[^(br)]>[A-zА-я ]*<|$", '> {{' + content + '}} <', line, count=1)
    return line


def tal_attributes_handler(line: str) -> str:
    attributes: str = re.findall("tal:attributes=[',\"](.+)[',\"]", line)[0]
    if not attributes:
        return line
    attributes: List[str] = attributes.split('; ')
    string_of_attrs = ''
    for attr in attributes:
        string_of_attrs += re.findall('(\w+) ', attr)[0]+'="{{'+(
                re.findall("python: ?(.+)", attr) or
                re.findall(" +(.+)", attr) or
                re.findall("request\.args\.get\('[A-z0-9/|.'() _]+'\)", attr)
        )[0]+'}}" '
    line = re.sub("tal:attributes=[',\"](.+)[',\"]", string_of_attrs, line)
    return line


def tal_repeat_handler(line: str) -> str:
    circle: List = re.findall("tal:repeat=[',\"]([^\"]+)[',\"]", line)
    if not circle:
        return line
    circle[0] = re.sub('python: *', '', circle[0])
    circle: List = circle[0].split(' ')
    if 'container' in circle[1]:
        content = re.findall("container\.(\w+)\(([A-z0-9='.() ,]*)\)", circle[1])[0]
        variables, query = get_bd_request(content)
        if query:
            circle[1]: str = re.sub(
                f"container\.\w+\([A-z0-9='.() ,]*\)",
                f'module.database.acquire(True).__enter__().execute("{query}", ({ ", ".join(variables)},))',
                circle[1]
            )
    line = re.sub("tal:repeat=[',\"]([^\"]+)[',\"]", '', line)
    return '{% for ' + circle[0] + ' in ' + circle[1] + ' %} \n' + line


def tal_define_handler(line: str) -> str:
    defines: List[str] = re.findall("tal:define=\"([^\"]+)\"", line)
    if not defines:
        return line
    line = re.sub("tal:define=\"([^\"]+)\"", '', line)
    defines: List[str] = defines[0].split(';')
    defines_vars, defines_values = [], []
    for d in defines:
        d = d.strip()
        defines_vars.append(re.findall('(\w+) ', d)[0])
        defines_values.append((re.findall("python: ?(.+)", d) or re.findall(" +(.+)", d) or re.findall("request\.args\.get\('[A-z0-9/|.'() _]+'\)", d))[0])
    return "{% set " + f"{', '.join(defines_vars)} = {', '.join(defines_values)}" + "%}\n" + line


def tal_replace_handler(line: str) -> str:
    replacement: List[str] = re.findall("<[^<]*tal:replace[^>]*>", line)
    if not replacement:
        return line
    replacement: str = replacement[0]
    replacement_data: str = re.findall("tal:replace=\"([^\"]*)\"", replacement)[0]
    replacement_data: str = (re.findall(" ?python: ?([^\"]+)", replacement_data) or
                             re.findall("([A-z0-9/|.'() ]+)", replacement_data))[0]
    return re.sub("<[^<]*tal:replace[^>]*>", f"{{{{{replacement_data}}}}}", line)


def handle_string_parameters(line: str) -> str:
    content: List[str] = re.findall('"(.+ % .+)"', line)
    if not content:
        return line
    line = re.sub('"(.+ % .+)"', 'content_here', line)
    for c in content:
        c = re.sub("{{(.*)}}", r"\1", c)
        param_string, params = c.split(' % ')
        params = re.sub("\((.*)\)", r"\1", params)
        params = re.sub(' ', '', params)
        for i in params.split(','):
            param_string = re.sub(r'%s', "{{" + i + "}}", param_string, count=1)
        param_string = re.sub('(\w+)\?', f'/{ITSD_name}/\\1/?', param_string)
        line = re.sub('content_here', param_string, line, count=1)
    return line


def get_bd_request(con: Union[Tuple[str, str], List[str]]) -> Tuple[Optional[List[str]], Optional[str]]:
    if f"{con[0]}.sql" in os.listdir(path):
        print(f'Заменяется {con[0]} с параметрами {con[1]}...')
        with open(f"{con[0]}.sql", 'r') as sql_file:
            statement: str = sql_file.read()
        statement: str = re.sub("\n", '', statement)
        variables: List[str] = re.findall("<dtml-sqlvar (\w+) [A-z \"=]+>", statement)
        for i in range(len(variables)):
            statement = re.sub(" *<dtml-sqlvar (\w+) [A-z \"=]+>", '?', statement)

        given_vars: List[str] = re.findall("(\w+) ?= ?[A-z0-9_.()']+", con[1])
        given_vars: Dict[str, str] = {j: re.findall(f"{j} ?= ?([A-z0-9_.()']+)", con[1])[0] for j in given_vars}
        variables_proccessed: List[str] = []
        for var in variables:
            variables_proccessed.append(str(given_vars.get(var)))
        return variables_proccessed, statement
    return None, None


def Polymorph_attributes_lowercase(text: str) -> str:
    containers: List[Tuple[str, str]] = re.findall("([A-z0-9_\[\]]+)\.([A-Z_0-9]+)", text)
    for con in containers:
        text = re.sub(f"{con[0]}.{con[1]}", f"{con[0]}.{con[1].lower()}", text)

    containers: List[Tuple[str, str]] = re.findall("([A-z_0-9\[\]]+)\['([A-Z_0-9]+)']", text)
    for con in containers:
        text = re.sub(f"{con[0]}\['{con[1]}']", f"{con[0]}.{con[1].lower()}", text)
    return text


handlers: Dict[str, callable] = {
    'tal:condition': tal_condition_handler,
    'tal:content': tal_content_handler,
    'tal:attributes': tal_attributes_handler,
    'tal:repeat': tal_repeat_handler,
    '%s': handle_string_parameters,
    'tal:define': tal_define_handler,
    'tal:replace': tal_replace_handler
}


if __name__ == '__main__':
    print('=' * 20)
    print('ZOPE MUST DIE!')
    print('=' * 20)

    path: str = os.path.dirname(os.path.abspath(__file__))
    print(f'Running {path}...')

    ITSD_name: str = input("Введите имя ИТСД(например, 'INFO'): ")

    for file in os.listdir(path):
        if file == __file__ or f'{path}/{file}' == __file__:
            continue
        if file.endswith('.html'):
            print(f'Обрабатывается шаблон {file}')
            with open(f"{path}/{file}", 'r') as f:
                html: str = f.read()
            html = re.sub('(?s)<html.*</head>',
                          "{% extends '" + ITSD_name + "/base.html' %}\n{% block content %}", html)
            html = re.sub('<html.*>', "{% extends '" + ITSD_name + "/base.html' %}\n{% block content %}", html)
            html = re.sub('</html>', "{% endblock %}", html)

            html: str = re.sub("options.get\(['\"](\w+)['\"]\)", "\\1", html)
            html: str = re.sub("options/(\w+)", "\\1", html)
            html: str = re.sub("options\[['\"](\w+)['\"]\]", "\\1", html)
            html: str = re.sub("request\.has_key\([\"'](\w+)[\"']\)", r"request.args.get('\1')", html)
            html: str = re.sub("request\.get\([\"'](\w+)[\"']\)", r"request.args.get('\1')", html)
            html: str = re.sub("request\.(\w+)", "request.args.get('\\1')", html)
            html: str = re.sub("request\.args\.get\('args'\)\.get", "request.args.get", html)
            html: str = re.sub("request\.args\.get\('get'\)", "request.args.get", html)
            html: str = re.sub("request/(\w+)", "request.args.get('\\1')", html)
            html: str = re.sub("request\[['\"](\w+)['\"]\]", "request.args.get('\\1')", html)

            html: str = re.sub("action=(['\"])(\w+)", f"action=\\1/{ITSD_name}/\\2/", html)

            jinja_template: str = ''
            for template_line in html.split('\n'):
                template_line: str = re.sub('metal:fill-slot="\w*"', '', template_line)
                template_line: str = re.sub('([^\'"|]) ?\| ?([^\'"|])', '\\1 or \\2', template_line)
                template_line: str = re.sub(' or nothing', "", template_line)
                for handler in handlers.keys():
                    if handler not in template_line:
                        continue
                    template_line = handlers[handler](template_line)
                jinja_template += template_line + "\n"

                jinja_template = Polymorph_attributes_lowercase(jinja_template)

            with open(f"{path}/{file}", 'w') as f:
                f.write(jinja_template)

        if file.endswith('.py'):
            print(f'\nОбрабатывается файл {file}\n')
            with open(f"{path}/{file}", 'r') as f:
                script: str = f.read()
            script = re.sub('request = container.REQUEST', "", script)
            script = re.sub('(RESPONSE|response) ?= ?request.RESPONSE', "", script)
            script = re.sub("(RESPONSE|response)\.redirect\((['\"])(\w+)\?", f"redirect(\\2/{ITSD_name}/\\3/?", script)
            script = re.sub("request\.has_key\([\"'](\w+)[\"']\)", r"request.args.get('\1')", script)
            script = re.sub("request\.get\([\"'](\w+)[\"']\)", r"request.args.get('\1')", script)
            script = re.sub("request\.(\w+)", r"request.args.get('\1')", script)
            script = re.sub("request\.args\.get\('args'\)\.get", "request.args.get", script)
            script = re.sub("request\[[\"'](\w+)[\"']\]", r"request.args.get('\1')", script)
            script = re.sub("request\.args\.get\('get'\)", "request.args.get", script)
            script = re.sub("['\"](\w+)['\"] +in +request", "request.args.get('\\1')", script)
            script = re.sub("container\.getId\(\)", f"'{ITSD_name}'", script)
            script = re.sub("<>", "!=", script)

            script = re.sub("(RESPONSE|response) ?= *request.args.get\('RESPONSE'\)", "", script)
            functions: List[str] = re.findall("def (\w+)\((.*)\)", script)
            for f in functions:
                script = re.sub(
                    f"def {f[0]}\({f[1]}\)",
                    f"""@module.route("/{f[0]}/", methods=["GET"], strict_slashes=False) \ndef {f[0]}({f[1]})""",
                    script
                )

            containers: List[str] = re.findall("return +(container|context)\.(\w+)\(([A-zА-я0-9='.() ,_%?&]*)\)", script)
            for con in containers:
                if f"{con[1]}.html" in os.listdir(path):
                    script = re.sub(
                        f"(context|container).{con[1]}\(",
                        f" render_template('{ITSD_name}/{con[1]}.html', ", script
                    )

            containers: List[Tuple[str, str, str]] = re.findall("= ?(context|container)\.(\w+)\(([A-z0-9='.() ,]*)\)", script)
            for con in containers:
                variables, query = get_bd_request((con[1], con[2]))
                if not query:
                    continue
                script = re.sub(
                    f"(\w+) ?= ?(context|container)\.{con[1]}\([A-z0-9='.() ,]*\)",
                    f"with module.database.acquire(True) as tr:\n    \\1 = tr.execute('{query}', ({', '.join(variables)},))",
                    script, count=1
                )

            containers: List[Tuple[str, str]] = re.findall("in +container\.(\w+)\(([A-z0-9='.() ,]*)\)", script)
            for con in containers:
                variables, query = get_bd_request(con)
                if not query:
                    continue
                script = re.sub(
                    f"for +(\w+) +in +container\.{con[0]}\([A-z0-9='.() ,]*\):",
                    f"with module.database.acquire(True) as tr:\n    for \\1 in tr.execute('{query}', ({', '.join(variables)},)):",
                    script, count=1
                )

            script = Polymorph_attributes_lowercase(script)

            with open(f"{path}/{file}", 'w') as f:
                f.write(script)

    print('\nCompleted!')
