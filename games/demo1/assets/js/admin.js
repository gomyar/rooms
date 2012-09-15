
var admin = {};


admin.loaded_script_file = null;
admin.loaded_chat_script_file = null;
admin.working_chat_script = null;

admin.load_script = function(script_file)
{
    admin.loaded_script_file = script_file;
    api_rooms.service_call("/admin/load_script", { "script_file": script_file }, admin.show_script_file);
}

admin.save_script = function(script_file, script_contents)
{
    api_rooms.service_call("/admin/save_script", { "script_file": script_file, "script_contents": script_contents }, admin.script_saved);
}

admin.script_saved = function(data)
{
    $(".scriptedit").remove();
    if (data.success)
        alert("Script saved");
    else
        alert(data.stacktrace);
}

admin.show_script_file = function(data)
{
    var textarea = $("<textarea>", {'class': 'editor', 'text': data, 'id': 'editarea' });
    $(".scriptedit").remove();
    var scriptedit_div = $("<div>", { "class": "scriptedit" }).append(
        textarea 
    );
    $("#main").append(scriptedit_div);

    var myCodeMirror = CodeMirror.fromTextArea(textarea[0], {'name': 'text/x-python'});
    scriptedit_div.append(
        $("<div>", {'class': 'savebutton', 'text': 'Save' }).click(function(){
            admin.save_script(admin.loaded_script_file, myCodeMirror.getValue())}
        ),
        $("<div>", {'class': 'closebutton', 'text': 'Close' }).click(function() { $(".scriptedit").remove() })
    );
}

admin.load_chat_script = function(script_file)
{
    admin.loaded_chat_script_file = script_file;
    api_rooms.service_call("/admin/load_chat_script", { "script_file": script_file }, admin.show_chat_script_file);
}

admin.show_chat_script_file = function(data)
{
    var chat = jQuery.parseJSON(data);
    admin.working_chat_script = chat;
    $(".chatedit").remove();
    var chatedit_div = $("<div>", { "class": "chatedit" });
    chatedit_div.append($("<div>", { "class": "chatcontainer" }).append(
        admin.create_chat_choice(chat))
    );

    chatedit_div.append(
        $("<div>", {'class': 'savebutton', 'text': 'Save' }).click(function(){
            console.log("Save");
        }),
        $("<div>", {'class': 'closebutton', 'text': 'Close' }).click(function() { $(".chatedit").remove() })
    );

    $("#main").append(chatedit_div);
}

admin.create_chat_choice = function(chat)
{
    var chat_div = $("<div>", { 'class': 'admin_chat_choice' });
    var chat_entry_div = $("<div>", {'class': 'chat_entry'});
    chat_entry_div.append($("<textarea>", { 'class': 'request', 'text': chat.request })).attr("chat", chat).change(function(e, data){ 
        $(this).attr("chat").request = this.textContent;
        console.log("changed to:"+admin.working_chat_script);
    });
    chat_entry_div.append($("<textarea>", { 'class': 'response', 'text': chat.response })).attr("chat", chat).change(function(e, data){ 
        $(this).attr("chat").response = this.textContent;
        console.log("changed to:"+admin.working_chat_script);
    });
    chat_entry_div.append($("<div>", { 'class': 'script_function', 'text': chat.script_function }));
    chat_entry_div.append($("<div>", {'class': 'choice_control'})).append(
        $("<div>", { 'class': 'button', 'text': 'Delete'}).click(function(e){ alert("Delete"); }),
        $("<div>", { 'class': 'button', 'text': 'Move up'}),
        $("<div>", { 'class': 'button', 'text': 'Move down'})
    );

    chat_entry_div.attr('chat', chat);
/*    chat_entry_div.click(function(e){
        var chat = e.attr('chat');
        admin.show_chat_editor(chat);
    });*/

    chat_div.append(chat_entry_div);
    var choices_div = $("<div>", {'class': 'choices' });
    for (c in chat.choices)
    {
        var choice = chat.choices[c];
        choices_div.append(admin.create_chat_choice(choice));
    }
    choices_div.append($("<div>", {'class': 'ccwrap'}).append($("<div>", {'class': 'choicecontrol', 'text': 'Add'})));
    chat_div.append(choices_div);
    return chat_div;
}

admin.show_chat_editor = function(chat)
{
    
}

admin.show_scripts = function(data)
{
    if ($(".evidence").length > 0)
        $(".evidence").remove();
    if ($(".scripts").length > 0)
        $(".scripts").remove();
    else
    {
        var scripts_div = $("<div>", { "class": "scripts"});

        var actor_scripts_div = $("<div>", { "class": "actor_scripts"});
        for (i in data.scripts)
        {
            var script_file = data.scripts[i];
            var script_element = $("<div>", {'class': 'scripts_file', 'text': script_file});
            script_element.attr('script_file', script_file);
            script_element.click(function (){
                console.log("Loading "+script_file);
                admin.load_script($(this).attr('script_file'));
            });

            actor_scripts_div.append(script_element);
        }
        actor_scripts_div.append($("<div>", {'class': 'buttonmenu'}).append(
            $("<div>", {'class': 'sbutton', 'text': 'Edit'}),
            $("<div>", {'class': 'sbutton', 'text': 'New'})
        ));
        var chats_div = $("<div>", { "class": "chat_scripts"});
        for (i in data.chat_scripts)
        {
            var script_file = data.chat_scripts[i];
            var script_element = $("<div>", {'class': 'scripts_file', 'text': script_file});
            script_element.attr('script_file', script_file);
            script_element.click(function (){
                console.log("Loading "+script_file);
                admin.load_chat_script($(this).attr('script_file'));
            });

            chats_div.append(script_element);
        }
        chats_div.append($("<div>", {'class': 'buttonmenu'}).append(
            $("<div>", {'class': 'sbutton', 'text': 'Edit'}),
            $("<div>", {'class': 'sbutton', 'text': 'New'})
        ));

        scripts_div.append(actor_scripts_div);
        scripts_div.append(chats_div);
        $("#main").append(scripts_div);
    }
}

admin.menu_scripts_clicked = function(e)
{
    api_rooms.service_call("/admin/list_scripts",
        { }, admin.show_scripts)
}


