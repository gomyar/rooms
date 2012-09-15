
admin_chat = {};

admin_chat.ChatEdit = function(chat)
{
    this.chat = chat;
    this.div = this.create_gui(chat);
    this.choices = [];

    for (c in chat.choices)
    {
        var choice = chat.choices[c];
        var choice_obj = new admin_chat.ChatEdit(choice);
        this.choices[this.choices.length] = choice_obj;
        this.choices_div.append(choice_obj.div);
    }
}

admin_chat.ChatEdit.prototype.create_gui = function(chat)
{
    var self = this;
    var div = $("<div>", {'class': "admin_chat_choice"}).append(
        $("<div>", {'class': 'chat_entry'}).append(
            $("<textarea>", {'class': "request", "text": chat.request}).change(function(e){
                self.chat.request = this.value;
                console.log("Changed to"+self.chat.request);
            }),
            $("<textarea>", {'class': "response", "text": chat.response}).change(function(e){
                self.chat.response = this.value;
                console.log("Changed to"+self.chat.response);
            })
        )
    );
    this.choices_div = $("<div>", {'class': 'choices' });
    div.append(this.choices_div);
    return div;
}

