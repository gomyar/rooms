
var logpanel = {};

logpanel.global = [];
logpanel.actor_logs = {};

logpanel.current_actor_id = null;

logpanel.init = function()
{
}

logpanel.add_log = function(actor_id, log_type, time, msg, stacktrace)
{
    if (!(actor_id in logpanel.actor_logs))
        logpanel.actor_logs[actor_id] = [];
    var logs = logpanel.actor_logs[actor_id];
    logs[logs.length] = {'msg': msg, 'time': time, 'log_type': log_type, 'stacktrace': stacktrace};

    if (!logpanel.current_actor_id || actor_id == logpanel.current_actor_id)
        logpanel.add_log_entry(actor_id, log_type, time, msg, stacktrace);
}

logpanel.show_log = function(actor_id)
{
    var panel = $("#logpanel");
    panel.empty();
    if (actor_id in logpanel.actor_logs)
        for (var i in logpanel.actor_logs[actor_id])
        {
            var entry = logpanel.actor_logs[actor_id][i];
            logpanel.add_log_entry(actor_id, entry.log_type, entry.time, entry.msg, entry.stacktrace);
        }
}

logpanel.add_log_entry = function(actor_id, log_type, time, msg, stacktrace)
{
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
    var lines = stacktrace.split("\n");
    var stack = [];
    for (var i in lines)
    {
        var line = lines[i];
        stack[stack.length] = div("stackline", {'text': line});
    }
    return stack;
}

logpanel.formatdate = function(time)
{   
    var date = new Date(time * 1000);
    return "" + date.getHours() + ":" + date.getMinutes() + ":" + (date.getSeconds() < 10 ? "0" + date.getSeconds() : date.getSeconds());
}
