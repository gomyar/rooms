

function logout()
{
    console.log("Logout");
    window.location = "/accounts/logout";
}

function init()
{
    console.log("init");
//    $(".hello .logout").click(logout)
}

$(document).ready(init);

