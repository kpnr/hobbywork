Grammar
=======

Expression: [type_prefix ':'] String

type_prefix: Name

.. note::
  default language is **Path**

.. note::
  Supported expression types
    #. path
    #. +exits
    #. nocall
    #. not
    #. string
    #. python

ExistsExpression: 'exists:' PathExpression

NoCallExpression: 'nocall:' PathExpression

NotExpression: 'not:' Expression

PathExpression: Path [ '|' Expression]

Path: Variable [ '/' PathSegment ]*

Variable: Name

PathSegment: ( '?' Variable ) | PathChar+

PathChar: AlphaNumeric | ' ' | '_' | '-' | '.' | ',' | '~'

.. note::
  Path examples:
    * request/cookies/oatmeal
    * nothing
    * context/some-file 2009_02.html.tar.gz/foo
    * root/to/branch | default
    * request/name | string:Anonymous Coward
    * context/?tname/macros/?mname

StringExpression: ( PlainString | [ VarSub ] )*

VarSub: ('$' Variable) | ( '${' Path '}' )

PlainString: ( '$$' | NonDollar )*

NonDollar: AnyCharExcept '$'

.. note::
  Examples:
    * string:$this and $that
    * string:total: ${request/form/total}
    * string:cost: $$$cost

Built-in Names
--------------
#. nothing
#. default
#. options
#. repeat
#. attrs
#. CONTEXTS - built-in variables
#. root - optional
#. context - optional
#. container - optional
#. template - optional
#. request - optional
#. user - optional
#. modules - optional

Optional supported by Zope, but not required by Tales

Builtins
---------

None abs apply callable chr cmp complex delattr divmod filter float
getattr hash hex int isinstance issubclass list len long map max
min oct ord repr round setattr str tuple

Available in Python expressions, but not in Python-based scripts:
  * path(string)  Evaluate a TALES path expression.
  * string(string) Evaluate a TALES string expression.
  * exists(string) Evaluates a TALES exists expression.
  * nocall(string) Evaluates a TALES nocall expression.

Boolean conversions
--------------------

- **false** is 0, '', empty sequence, **void**, **None**, **Nil**, **NULL** and
  other non-values
- **true** is positive & negative numbers, non-empty string and sequence
