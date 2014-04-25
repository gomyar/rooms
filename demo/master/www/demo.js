
var methods = {};


function show_games(data)
{
    console.log("Show games");
    console.log(data);
}

function show_methods(data)
{
    console.log("Show methods");
    console.log(data);
    methods = data;
    $("#methods").remove();
    var methods_div = $("<div>", {'id': 'methods'});
    for (var c in data)
    {
        var controller = data[c];
        var controller_div = $("<div>", {'class': 'controller', 'text': c, 'id': c});
        for (var m in controller)
        {
            var method = controller[m];
            var method_div = $("<div>", {'class': 'method', 'id': m});
            var params_div = $("<div>", {'class': 'params'});
            for (var a in method.args)
            {
                if (a > 0)
                    params_div.append($("<label>", {"text": ', '}));
                params_div.append($("<label>", {'class': "argname", "text": method.args[a]}));
                params_div.append($("<input>", {'class': "arg", 'id': method.args[a]}));
            }

            method_div.append(
                $("<div>", {'class': 'name', 'text': m}).append(
                    $("<div>", {'class': 'call', 'text': "Call >>"}).bind("click", {"controller": c, "method": m}, perform_call)
                )
            );
            if (method.doc)
                method_div.append($("<div>", {"class": "doc", "text": method.doc}));
            method_div.append(params_div);
            controller_div.append(method_div);
        }
        methods_div.append(controller_div);
    }
    $('body').append(methods_div);
}

function perform_call(e)
{
    var controller = e.data.controller;
    var method = e.data.method;

    var args = {};

    for (var a in methods[controller][method].args)
    {
        var arg = methods[controller][method].args[a];
        var arg_input = $("#methods .controller#" + controller + " .method#" + method + " .params input#"+arg);
        args[arg] = arg_input.val();
    }
    console.log(args);
    perform_post("/" + controller + "/" + method, args, show_call_results, show_call_error);
}

function show_call_results(data)
{
    var text = JSON.stringify(data, null, 4);
    text = text.replace(/\n/g, "<br>");
    text = text.replace(/ /g, "&nbsp");
    text = text.replace(/\t/, "&nbsp");
    $("#result").remove();
    $("body").append(
        $("<div>", {"id": "result"}).html(text)
    );
}

function show_call_error(error, jqxhr)
{
    var text = jqxhr.responseText;
    text = text.replace(/\n/g, "<br>");
    text = text.replace(/ /g, "&nbsp");
    text = text.replace(/\t/, "&nbsp");
    $("#result").remove();
    $("body").append(
        $("<div>", {"id": "result", "class": "error"}).html(text)
    );

}

function init()
{
    console.log("init");
    perform_post("/master/all_games", {}, show_games);
    perform_post("/_list_methods", {}, show_methods);
}

$(document).ready(init);
