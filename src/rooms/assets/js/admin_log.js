
var logpanel = {};

logpanel.global = [];
logpanel.actor_logs = {};

logpanel.init = function()
{
}

logpanel.add_log = function(actor_id, log_type, time, msg, stacktrace)
{
    if (actor_id in logpanel.actor_logs)
    {
        var logs = logpanel.actor_logs[actor_id];
        logs[logs.length] = msg;
    }
    else
        logpanel.actor_logs[actor_id] = [msg];

    var panel = $("#logpanel");
    var scrollToBottom = false;
    if (panel.height() + panel[0].scrollTop - panel[0].scrollHeight > 10)
        scrollToBottom = true;
    panel.append(
        div("logentry " + log_type).append(
            div("time", {'text': logpanel.formatdate(time) }),
            div("name", {'text': api_rooms.actors[actor_id].name }),
            div("type", {'text': api_rooms.actors[actor_id].actor_type }),
            logpanel.logmessage(msg, stacktrace)
        )
    );
    if (scrollToBottom)
        panel[0].scrollTop = panel[0].scrollHeight
}

logpanel.logmessage = function(msg, stacktrace)
{
    if (stacktrace)
        return div("msg").append(
            logpanel._format_stacktrace(stacktrace)
        );
    else
        return div("msg", {'text': msg});
}

logpanel._format_stacktrace = function(stacktrace)
{
    if (stacktrace)
    {
        var lines = stacktrace.split("\n");
        var stack = [];
        for (var i in lines)
        {
            var line = lines[i];
            stack[stack.length] = div("stackline", {'text': line});
        }
        return stack;
    }
    else
        return ""
}

logpanel.formatdate = function(time)
{   
    var date = new Date(time * 1000);
    return "" + date.getHours() + ":" + date.getMinutes() + ":" + (date.getSeconds() < 10 ? "0" + date.getSeconds() : date.getSeconds());
}
