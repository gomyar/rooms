from django.shortcuts import render
from django.contrib.auth.decorators import permission_required
from django.shortcuts import render_to_response


@permission_required("is_staff")
def index(request):
    return render_to_response("rooms_mapeditor/index.html")
