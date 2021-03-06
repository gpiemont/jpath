## -*- coding: utf-8 -*-
##
##  Copyright (c) 2021, Giulio Piemontese <gpiemont at sdf.org>
##  All rights reserved.
##
##  Redistribution and use in source and binary forms, with or without
##  modification, are permitted provided that the following conditions are met:
##  1. Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##  2. Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in the 
##     documentation and/or other materials provided with the distribution.
##  3. Neither the name of the <organization> nor the 
##     names of its contributors may be used to endorse or promote products
##     derived from this software without specific prior written permission.
##
##  THIS SOFTWARE IS PROVIDED BY <COPYRIGHT HOLDER> ''AS IS'' AND ANY 
##  EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
##  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE 
##  DISCLAIMED. IN NO EVENT SHALL <COPYRIGHT HOLDER> BE LIABLE FOR ANY 
##  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
##  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
##  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND 
##  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
##  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
##  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
##

import json
import re

##
##  JPath   : Experimental JSON-Meta accessor and parser
##
##  Access JSON objects via a custom, XPath or C-like syntax 
##
##  Given a JSON/dict object in the form :
##

d = {
        "test" : {
            "path" : [
                {
                    "to" : [
                        {
                            "object5" : 1,
                        },
                        [ 0, 1, 2 ]
                    ],
                    "in" : [
                        {
                            "arrays" : [
                                {
                                    "test" : 7,
                                    "\"\"" : 42
                                }
                            ]
                        },
                    ]
                }
            ],
            "inner" : None,
        }
}

##
## or a List/Array in the form
##

a = [ 
        [ 
            [ 0, 0, 0 ], 
            [ 1, 2, 3 ],
            [ 0, 0, 0 ],
        ],
        [ 
            [ 1, 0, 0 ], 
            [ 0, 1, 0 ],
            [ 0, 0, 1 ],
        ],
    ]

##
## return the element pointed to by a custom C-like link:
##
##  <object | [subscript]> [-> <objectN | [subscript]> [-> <objectM | [subscript] [..]>]]
##
##  where ``object'' can be a JSON/dict string key or subscript in turn,
##
##  and ``subscript'' is defined as:
##
##      subscript := [idx := integer | key := (string|integer) ] 
##
##  E.g.
##
##      value = test->path[0]->to->object
##

##
## Compiled regexp(s) used to identify subscripts, apex and bracket pairs.
##

##
## LEGAL values for subscript in arrays are numerical characters.
## LEGAL values for subscript in dict are: alphanumeric characters and spaces.
##
## Everything else leads to a KeyError or TypeError exception
##

subscript_re = re.compile(r"((\[\d+\])+|((\[\"(\w+|\d+|\s*)+\"\])+|(\[\'(\w+|\d+|\s*)+\'\])+)+)+")
apex_re      = re.compile(r"(^\'|\'$)+|(^\"|\"$)+")
brackets_re  = re.compile(r"[\[\]]")

##
## Default nil value
##

nil = {"result" : "error"}

def jpath(source: dict, path: str, keytypes=[str, int], null=nil, sep='->'):

    """
    Return a value inside a dict/JSON object from a given path specifications.
    XXX : Non-recursive version.

    @source : source dict/JSON object
    @path   : link specification

    @keytypes   : try this types in sequence for subscripts keytypes.
    @null       : default value for 'nil' symbol.

    """

    if not path:
        # Terminal case
        return source

    ##
    ## Compute components from linkpath
    ##

    elems = path.split(sep)

    ##
    ## Initialize object to default 'nil' value
    ##

    obj = null

    try:
        for elem in elems:
            
            #
            # (0) Iterate over link/path element
            #

            if not elem:
                # Sanitize (0)
                continue

            #
            # Zero the root key of an element
            #
            root = None

            subscripts = subscript_re.search(elem)

            if subscripts:
                # 
                # (0.0) Element has subscript, process them along with element name
                #

                if not root:
                    #
                    # (0.0.1) Find root element name, e.g. test[0] => "test"
                    #

                    root = subscript_re.sub("", elem)

                    if not root:
                        #
                        # Root element name cannot be desumed, probably a pure subscript has been supplied.
                        # Use obj as root element or source, if no obj has been computed.
                        #
                        if obj == null:
                            obj = source
                    else:
                        #
                        # Object now points to the root element
                        #

                        obj = source[root] if obj == null else obj[root]


                #
                # (0.1) Look for every subscript in root
                #

                scs = [ i for i in brackets_re.split(subscripts.group()) if i ]

                for subscript in scs:
                    #
                    # (0.1.0) Iterate over found (and consecutive) subscripts
                    #

                    #print(f"Subscript : {subscript}")
                
                    try:
                        # Force keys to integer, XXX Others?
                        sc = int(subscript)
                    except:
                        sc = apex_re.sub("", str(subscript))
                    
                    #
                    # Update object with subscripted element
                    #
                        
                    if not isinstance(obj, (list, dict)):
                        raise TypeError(f"'{sc}' : invalid subscript")
                    
                    obj = obj[sc] if obj != null else source[sc]

                continue

            #
            # (0.2) Move to the next element
            #
            if not isinstance(obj, (list, dict)):
                raise TypeError(f"'{obj}' : non-subscriptable object")

            if not keytypes:
                #
                # Try with string keys, first
                #
                keytypes = [ str, int ]

            for k in keytypes:
                try:
                    if obj != null:
                        obj = obj[k(elem)]
                    else:
                        obj = source[k(elem)]
                        
                except (IndexError, KeyError):
                    # Object is null on IndexError/KeyError    
                    obj = null
                except:
                    pass

    except (IndexError, KeyError, TypeError):
        obj = null
    except BaseException as e:
        # Element not found
        # raise e
        pass

    return obj

def jxpath(source: dict, path: str, keytypes=[str, int], null=nil):

    """
    Return a value inside a dict/JSON object from a given path specifications, 
    using a XPath-like syntax
    
    """
    
    return jpath(source, path, keytypes=keytypes, null=nil, sep='/')

##
## The default programmatic access
##

# try:
#     value = d["test"]["path"][0]["to"]["0"]["object"]
#     print(f"Value : {value}")
# except:
#     pass

##
## Testcase linkset
##

testcases = [
#
# Source    Json Link                                  Eval
#
    (d,     "test->path[0]->to[0]->object5",           d["test"]["path"][0]["to"][0]["object5"]),
    (d,     "test->path[0]->to[0]->object5[7]",        nil),
    (d,     "test->path[0]->to[0]->object5[7][0]",     nil),
    (d,     "test->path[0]->to[0]->object5->abc",      nil),
    (d,     "test->path[0]->to[1][2]",                 d["test"]["path"][0]["to"][1][2]),
    (d,     "test->inner",                             d["test"]["inner"]),
    (d,     "test['path']",                            d["test"]["path"]),  # Legal, regular syntax
    (d,     "test[path]",                              nil),  # Illegal, mixes regular and alternate syntax
    ##
    ## Mixed subscripts.
    ##  NOTE ->key and ['key'] are equivalent
    ##
    (d,     "test->path[0]->in[0]->arrays[0]['test abc']",  nil),
    (d,     "test->path[0]->in[0]->arrays[0][\"\"]",        nil),
    (d,     "test->path[0]->in[0]->arrays[1]",              nil),
    (d,     "test->path[0]->in[0]->arrays[0]->test",        d["test"]["path"][0]["in"][0]["arrays"][0]["test"]),
    (d,     "['test']['path'][0][\"to\"][0][\"object5\"]",  d["test"]["path"][0]["to"][0]["object5"]),
    (d,     "['test']['path'][0][\"to\"][0]",               d["test"]["path"][0]["to"][0]),
    (d,     "['test']['path'][0]['to'][5]",                 nil),
    (d,     "test->path[5]->in[0]->arrays[0]['test abc']",  nil),
    ##
    ## Pure Array subscript/key access
    ##
    (a,     "[0][1][1]",                                    a[0][1][1]),
    (a,     "0->1->1",                                      a[0][1][1]),
    (a,     "0->1",                                         a[0][1]),
    (a,     "9",                                            nil)
]

testcases_jx = [
    (d,     "//test/path[0]/in[0]/arrays[0]",                d["test"]["path"][0]["in"][0]["arrays"][0]),
    (d,     "//test/path[0]/in[0]/arrays[0]/test",           d["test"]["path"][0]["in"][0]["arrays"][0]["test"]),
    (d,     "//test/path[0]/to[0]",                          d["test"]["path"][0]["to"][0])
]

if __name__ == "__main__":

    print(json.dumps(d, indent=4))

    passed = 0
    fails  = 0
    value = nil

    msg = "OK"

    for testset in (testcases, testcases_jx):

        total = len(testset)

        for source, tl, evals in testset:
            print(f"[EVAL]  Rule : {tl:<45}", end='')

            if testset == testcases:
                value = jpath(source, tl)
            else:
                value = jxpath(source, tl)

            if value == evals:
                passed += 1
                msg = "OK"
            else:
                fails += 1
                msg = f"FAIL (value : {value}, expected : {evals}"

            print(f"\t{msg}\n")

        print(f"[RESULT]    Fails  : {fails}/{total}")
        print(f"[RESULT]    Passed : {passed}/{total}")
            
        passed = fails = 0

