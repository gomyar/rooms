
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
    this.choices_div = $("<div>", {'class': 'choices' });

    var div = $("<div>", {'class': "admin_chat_choice"}).append(
        $("<div>", {'class': 'choice_control'}).append(
            $("<div>", { 'class': 'button', 'text': 'Delete'}),
            $("<div>", { 'class': 'button', 'text': 'Move up'}),
            $("<div>", { 'class': 'button', 'text': 'Move down'})
        ),
        $("<div>", {'class': 'chat_entry'}).append(
            $("<textarea>", {'class': "request", "text": chat.request}).change(function(e){
                self.chat.request = this.value;
                console.log("Changed to"+self.chat.request);
            }),
            $("<textarea>", {'class': "response", "text": chat.response}).change(function(e){
                self.chat.response = this.value;
                console.log("Changed to"+self.chat.response);
            }),
            this.choices_div,
            $("<div>", {'class': 'ccwrap'}).append(
                $("<div>", {'class': 'add_button', 'text': 'Add'}).click(function(e){self.add_clicked(self.chat);})
            )
        )
    );

    return div;
}

admin_chat.ChatEdit.prototype.add_clicked = function(chat)
{
    console.log("Adding to chat "+chat.request);
    var new_chat = {'request': '', 'response': '', 'script_function': '', 'choices': []};
    var new_obj = new admin_chat.ChatEdit(new_chat);
    if (chat.choices == null)
        chat.choices = [];
    chat.choices[chat.choices.length] = new_chat;
    this.choices[this.choices.length] = new_obj;
    this.choices_div.append(new_obj.div);
}
