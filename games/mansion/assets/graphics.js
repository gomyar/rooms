
var images = {};

function loadImages(imagemap, callback)
{
    var count = 0;
    for (i in imagemap)
    {
        var image = new Image();
        image.src = imagemap[i];
        image.onload = function () {
            count --;
            if (count <= 0)
                callback();
        };
        images[i] = image;
        count ++;
    }
}

