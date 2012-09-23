
var gui_screens = {};

gui_screens.show_chat_window = function(message)
{
    gui.requestRedraw();
    $("#chatOuter").remove();
    if (message.command == "end_chat")
    {
        return;
    }
    console.log("Start chat with: "+message);
    var chatChoices = $("<div>", {'id': 'chatChoices'});
    for (i in message.choices)
    {
        var choice = message.choices[i];
        var choice_div = $("<div>", { "class": "chatChoice" });
        choice_div.text(choice);
        $(choice_div).attr('choice', choice);
        choice_div.click(function(e){
            api_rooms.chat(message.actor_id, $(this).attr('choice'), gui_screens.show_chat_window);
        });
        chatChoices.append(choice_div);
    }
    var chatDiv = $("<div>", {'id': 'chatOuter'}).append(
        $("<div>", {'id': 'chatText', 'text': message.msg}),
        chatChoices
    );
    chatDiv.css("left", $(window).width() / 2 - 175);
    $("#main").append(chatDiv);
}

