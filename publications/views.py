from django.shortcuts import render
from publications.models import Publication


def publication_index(request):

    publications = Publication.objects.all()

    context = {

        'publications': publications

    }

    return render(request, 'publication_index.html', context)

def publication_detail(request, pk):

    publication = Publication.objects.get(pk=pk)

    context = {

        'publication': publication

    }

    return render(request, 'publication_detail.html', context)
