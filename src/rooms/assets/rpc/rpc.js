
var methods = {};
var websocket = null;


perform_get = function(url, callback, onerror)
{
    $.ajax({
        'url': url,
        'success': function(data) {
            if (callback != null)
                callback(data);
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
            if (onerror)
                onerror(errorText, jqXHR);
        },
        'type': 'GET'
    });
}


perform_post = function(url, data, callback, onerror)
{
    $.ajax({
        'url': url,
        'data': data,
        'success': function(data) {
            if (callback != null)
                callback(data);
        },
        'error': function(jqXHR, errorText) {
            console.log("Error calling "+url+" : "+errorText);
            if (onerror)
                onerror(errorText, jqXHR);
        },
        'type': 'POST'
    });
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

            if (method.type == "request")
            {
                var call_input = $("<div>", {'class': 'call', 'text': "Call >>"});
                call_input.bind("click", {"controller": c, "method": m}, perform_call);
            }
            else if (method.type == "websocket")
            {
                var call_input = $("<div>", {'class': 'callsocket', 'text': 'Connect >>'});
                call_input.bind("click", {"controller": c, "method": m}, connect_websocket);
            }
            method_div.append(
                $("<div>", {'class': 'name', 'text': m}).append(
                    call_input
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

function connect_websocket(e)
{
    var controller = e.data.controller;
    var method = e.data.method;

    var args = "";

    for (var a in methods[controller][method].args)
    {
        var arg = methods[controller][method].args[a];
        var arg_input = $("#methods .controller#" + controller + " .method#" + method + " .params input#"+arg);
        args = args + arg + "=" + arg_input.val() + "&";
    }
   
    if (websocket)
        websocket.close();

    websocket = new WebSocket("ws://"+window.location.hostname+":"+window.location.port+"/" + controller + "/" + method + "?" + args);
    websocket.onmessage = websocket_callback;
    websocket.onopen = websocket_onopen;
    websocket.onclose = websocket_onclose;
    websocket.onerror = websocket_onerror;

    $("#websocket").remove();
    $("body").append($("<div>", {"id": "websocket"}));
}

function websocket_callback(msg)
{
    if (msg.data)
        $("#websocket").append($("<div>", {"class": "msg", "text": msg.data}));
}

function websocket_onopen()
{
    $("#websocket").append($("<div>", {"class": "msgctrl", "text": "Connection opened"}));
}

function websocket_onclose()
{
    $("#websocket").append($("<div>", {"class": "msgctrl", "text": "Connection closed"}));
}

function websocket_onerror(e)
{
    console.log(e);
    $("#websocket").append($("<div>", {"class": "msgerr", "text": "Connection error"}));
}

function show_call_results(data)
{
    var text = JSON.stringify(data, null, 4);
    text = text.replace(/\n/g, "<br>");
    text = text.replace(/ /g, "&nbsp");
    text = text.replace(/\t/, "&nbsp");
    $("#result").remove();
    $("body").append(
        $("<div>", {"id": "result"}).html(text).fadeIn()
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
        $("<div>", {"id": "result", "class": "error"}).html(text).fadeIn()
    );

}

function init()
{
    console.log("init");
    perform_post("/_list_methods", {}, show_methods);
}

$(document).ready(init);
