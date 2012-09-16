
admin_chat = {};

admin_chat.ChatEdit = function(chat, show_controls)
{
    this.chat = chat;
    if (show_controls)
        this.div = this.create_gui(chat);
    else
        this.div = this.create_root_gui(chat);
    this.choices = [];
    this.parent_edit = null;
    this.offset = 0;

    for (offset in chat.choices)
    {
        var choice = chat.choices[offset];
        var choice_obj = new admin_chat.ChatEdit(choice, true);
        choice_obj.parent_edit = this;
        choice_obj.offset = offset;
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
            $("<div>", { 'class': 'button', 'text': 'Delete'}).click(function(e){ self.delete_clicked(); }),
            $("<div>", { 'class': 'button', 'text': 'Move up'}).click(function(e){ self.moveup_clicked(); }),
            $("<div>", { 'class': 'button', 'text': 'Move down'}).click(function(e){ self.movedown_clicked(); })
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
                $("<div>", {'class': 'add_button', 'text': 'Add'}).click(function(e){self.add_clicked();})
            )
        )
    );

    return div;
}


admin_chat.ChatEdit.prototype.create_root_gui = function(chat)
{
    var self = this;
    this.choices_div = $("<div>", {'class': 'choices' });

    var div = $("<div>", {'class': "admin_chat_choice"}).append(
        $("<div>", {'class': 'chat_entry'}).append(
            this.choices_div,
            $("<div>", {'class': 'ccwrap'}).append(
                $("<div>", {'class': 'add_button', 'text': 'Add'}).click(function(e){self.add_clicked();})
            )
        )
    );

    return div;
}

admin_chat.ChatEdit.prototype.add_clicked = function()
{
    console.log("Adding to chat "+this.chat.request);
    var new_chat = {'request': '', 'response': '', 'script_function': '', 'choices': []};
    var new_obj = new admin_chat.ChatEdit(new_chat, true);
    new_obj.parent_edit = this;
    if (this.chat.choices == null)
        this.chat.choices = [];
    this.chat.choices[this.chat.choices.length] = new_chat;
    this.choices[this.choices.length] = new_obj;
    this.choices_div.append(new_obj.div);
}

admin_chat.ChatEdit.prototype.delete_clicked = function()
{
    if (confirm("Delete " + this.chat.request + "?"))
    {
        if (this.parent_edit.choices.length > this.offset)
        {
            this.parent_edit.choices.pop(this.offset);
            this.parent_edit.chat.choices.pop(this.offset);
        }
        for (offset in this.parent_edit.choices)
            this.parent_edit.choices[offset].offset = offset;
        this.div.remove();
    }
}

admin_chat.ChatEdit.prototype.moveup_clicked = function()
{
    if (this.offset > 0)
    {
        this.parent_edit.choices[this.offset] = this.parent_edit.choices[this.offset - 1];
        this.parent_edit.choices[this.offset - 1] = this;
        this.parent_edit.chat.choices[this.offset] = this.parent_edit.chat.choices[this.offset - 1];
        this.parent_edit.chat.choices[this.offset - 1] = this.chat;

        this.div.insertBefore(this.parent_edit.choices_div.children()[this.offset-1]);

        for (offset in this.parent_edit.choices)
            this.parent_edit.choices[offset].offset = offset;
    }
}

admin_chat.ChatEdit.prototype.movedown_clicked = function()
{
    if (this.offset < this.parent_edit.choices.length - 1)
    {
        this.parent_edit.choices[this.offset] = this.parent_edit.choices[parseInt(this.offset) + 1];
        this.parent_edit.choices[parseInt(this.offset) + 1] = this;
        this.parent_edit.chat.choices[this.offset] = this.parent_edit.chat.choices[parseInt(this.offset) + 1];
        this.parent_edit.chat.choices[parseInt(this.offset) + 1] = this.chat;

        this.div.insertAfter(this.parent_edit.choices_div.children()[parseInt(this.offset) + 1]);

        for (offset in this.parent_edit.choices)
            this.parent_edit.choices[offset].offset = offset;
    }
}
