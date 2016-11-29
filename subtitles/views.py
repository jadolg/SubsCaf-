#-*-coding:utf-8-*-
from __future__ import unicode_literals
from os import remove, mkdir

import operator
from rexec import FileWrapper

from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.http.response import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from os.path import splitext, basename
from hashlib import sha256
from shutil import copy, rmtree
import zipfile
import fnmatch
import os
from unidecode import unidecode
import unicodedata

from SubsDB.settings import TMP_FOLDER, STASH_FOLDER
from subtitles.models import Subtitulo
from subtitles.util import id_generator

EXTENSIONES = ['.srt', '.sub', '.ass', '.zip']


def index(request):
    return render(request, 'index.html')


def search(request):
    q = ''

    if request.GET.has_key('q') and request.GET['q'] != '':
        q = request.GET['q']
        paginator = Paginator(search_keywords(Subtitulo,q.split()), 10)
        # paginator = Paginator(Subtitulo.objects.filter(nombre__search=q), 10)
        page = request.GET.get('page')

        try:
            subs = paginator.page(page)
        except PageNotAnInteger:
            subs = paginator.page(1)
        except EmptyPage:
            subs = paginator.page(paginator.num_pages)
    else:
        return HttpResponseRedirect('/')

    return render(request, 'search.html', {'subs':subs, 'search_term':q})


def upload(request):
    if request.method == 'POST':
        try:
            if request.FILES.has_key('afile'):
                afile = request.FILES['afile']
                fname,ext = splitext(afile.name)
                rand_name = id_generator()
                path = TMP_FOLDER + rand_name

                with open(path, 'wb+') as destination:
                    for chunk in afile.chunks():
                        destination.write(chunk)

                if ext in EXTENSIONES:
                    if ext == '.zip':
                        # archive = zipfile.ZipFile(path)
                        aux_ext_path = TMP_FOLDER+rand_name+'_ext'
                        mkdir(aux_ext_path)
                        unzip_all(path, aux_ext_path)
                        # archive.extractall(aux_ext_path)
                        remove(path)

                        matches = []
                        for root, dirnames, filenames in os.walk(aux_ext_path):
                            for filename in fnmatch.filter(filenames, '*.srt'):
                                matches.append(os.path.join(root, filename))
                            for filename in fnmatch.filter(filenames, '*.sub'):
                                matches.append(os.path.join(root, filename))
                            for filename in fnmatch.filter(filenames, '*.ass'):
                                matches.append(os.path.join(root, filename))
                        count = 0
                        for i in matches:
                            d = open(i, "rb").read()
                            thash = sha256(d)
                            sha = thash.hexdigest()

                            if len(Subtitulo.objects.filter(ahash=sha)) == 0:
                                copy(i, STASH_FOLDER + sha)
                                Subtitulo(nombre=unidecode(basename(i)), ruta=sha, ahash=sha).save()
                                count += 1

                        messages.add_message(request, messages.SUCCESS, "Se han agregado "+str(count)+" subtítulos nuevos")
                        if count < len(matches):
                            messages.add_message(request, messages.INFO, "Se omitieron "+str(len(matches)-count)+" subtítulos que ya estaban en la colección")

                        rmtree(TMP_FOLDER+rand_name+'_ext')
                    else:
                        d = open(path, "rb").read()
                        thash = sha256(d)
                        sha = thash.hexdigest()

                        if len(Subtitulo.objects.filter(ahash=sha)) > 0 :
                            messages.add_message(request, messages.WARNING,"Ya tenemos este subtítulo. Gracias por compartir")
                        else:
                            copy(path,STASH_FOLDER+sha)
                            remove(path)
                            Subtitulo(nombre=unidecode(afile.name), ruta=sha, ahash=sha).save()
                            messages.add_message(request, messages.SUCCESS, "Subtítulo agregado correctamente")
                else:
                    messages.add_message(request, messages.ERROR, "Los tipos de fichero permitidos son .srt | .sub | .ass | .zip")
            else:
                messages.add_message(request, messages.ERROR, "No ha incluido ningún fichero")
        except:
            messages.add_message(request, messages.ERROR, "Ha ocurrido un error mientras se procesaba el fichero")


    return render(request, 'upload.html')


def download(request,id):
    subtitulo = Subtitulo.objects.get(id=id)
    subtitulo.descargas += 1
    subtitulo.save()
    response = HttpResponse(FileWrapper(open(STASH_FOLDER+subtitulo.ruta, 'rb')),
                            content_type='text/plain')
    nombre = '"' + subtitulo.nombre + '"'

    response['Content-Disposition'] = 'attachment; filename=' + nombre + ';'
    return response


def search_keywords(subs, keywords):
    if isinstance(keywords, str):
        keywords = [keywords]

    if not isinstance(keywords, list):
        return None

    nameSearch = [Q(nombre__icontains=x) for x in keywords]

    r_qs = subs.objects.filter(reduce(operator.and_,nameSearch)).order_by("-descargas","nombre")
    return r_qs


def unzip_all(azipfile, ext_path):
    zf = zipfile.ZipFile(azipfile, 'r')
    for m in zf.infolist():
        data = zf.read(m)
        #this is not a solution
        #Fix this properly
        try:
            print ext_path + '/' + unicodedata.normalize('NFKD', unicode(m.filename)).encode('ascii', 'ignore')
            disk_file_name = ext_path + '/' + unicodedata.normalize('NFKD', unicode(m.filename)).encode('ascii',
                                                                                                        'ignore')
        except:
            print 'unicode error'

        try:
            print ext_path + '/' + m.filename.decode('unicode_escape').encode('ascii', 'ignore')
            disk_file_name = ext_path + '/' + m.filename.decode('unicode_escape').encode('ascii', 'ignore')
        except:
            print 'unicode error 2'

        # disk_file_name = ext_path+'/'+ m.filename.decode('unicode_escape').encode('ascii','ignore')
        #disk_file_name = ext_path + '/' + unicodedata.normalize('NFKD', unicode(m.filename)).encode('ascii', 'ignore')
        dir_name = os.path.dirname(disk_file_name)
        try:
            os.makedirs(dir_name)
        except OSError as e:
            if e.errno == os.errno.EEXIST:
                pass
            else:
                raise
        except Exception as e:
            raise
        try:
            with open(disk_file_name, 'wb') as fd:
                fd.write(data)
        except:
            pass
    zf.close()