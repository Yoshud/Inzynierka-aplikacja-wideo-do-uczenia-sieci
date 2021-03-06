from django.db import models
from django.utils import timezone
import os


class Status(models.Model):
    status = models.CharField("status", max_length=100, unique=True)

    class Meta:
        abstract = True

    def __str__(self):
        return self.status


class StatusFilmu(Status):
    pass


class StatusPozycji(Status):
    pass


class StatusPozycjiCrop(Status):
    pass


class Kolor(models.Model):
    nazwa = models.CharField("nazwa", max_length=100, null=True, blank=True, unique=True)
    kod = models.CharField("kod", max_length=100, null=True, blank=True)

    def __str__(self):
        return self.nazwa


class ZbiorKolorow(models.Model):
    nazwa = models.CharField("nazwa", max_length=100, null=True, blank=True, unique=True)
    kolory = models.ManyToManyField("Kolor", blank=True)
    domyslny_kolor = models.ForeignKey(
        "Kolor", related_name="zbior_domyslny_kolor", blank=True, null="True", on_delete=models.SET_NULL
    )


class Punkt(models.Model):
    x = models.IntegerField("x", default=0, null=True, blank=True)
    y = models.IntegerField("y", default=0, null=True, blank=True)

    class Meta:
        abstract = True

    def getPosition(self):
        if self.x is not None and self.y is not None:
            return self.x, self.y
        else:
            return None


class PozycjaPunktu(Punkt):
    klatka = models.ForeignKey("Klatka", related_name="pozycja", on_delete=models.CASCADE)
    status = models.ForeignKey("StatusPozycji", related_name="pozycja", on_delete=models.CASCADE, blank=True, null=True)
    kolor = models.ForeignKey("Kolor", related_name="pozycja", on_delete=models.CASCADE, blank=True, null=True)


class PozycjaPunktuPoCrop(models.Model):
    obraz = models.OneToOneField("ObrazPoDostosowaniu", related_name="pozycja", on_delete=models.CASCADE)
    json = models.TextField(default="")


class PozycjaCropa(Punkt):
    pass


class Klatka(models.Model):
    film = models.ForeignKey("Film", related_name="film", on_delete=models.CASCADE)
    nr = models.IntegerField(default=0)
    sciezka = models.TextField(default="", blank=True, null=True)
    data = models.DateTimeField(default=timezone.now)
    nazwa = models.TextField(default="", blank=True, null=True)

    def getPath(self):
        if self.sciezka:
            return self.sciezka
        elif self.nazwa:
            return os.path.join(self.film.sesja.folderZObrazami.getPath(), self.nazwa)
        else:
            raise AttributeError("Not defined sciezka and nazwa")


class Film(models.Model):
    sciezka = models.TextField(blank=True, null=True)
    nazwa = models.CharField("nazwa", max_length=80, blank=True, null=True)
    FPS = models.FloatField("fps", default=0.0)
    dlugosc = models.TimeField("dlugosc", blank=True, null=True)
    rozmiarX = models.IntegerField("x", default=0)
    rozmiarY = models.IntegerField("y", default=0)
    iloscKlatek = models.IntegerField("iloscKlatek", blank=True, null=True)
    data = models.DateTimeField(default=timezone.now)
    status = models.ManyToManyField("StatusFilmu", blank=True)
    sesja = models.ForeignKey("Sesja", on_delete=models.CASCADE)


class FolderZObrazami(models.Model):
    sciezka = models.TextField(default="", blank=True, null=True)
    nazwa = models.TextField(default="", blank=True, null=True)

    def getPath(self) -> str:
        if self.sciezka:
            return self.sciezka
        elif self.nazwa:
            return os.path.join(self.sesja.sciezka, self.nazwa)
        else:
            raise AttributeError("Not defined sciezka and sesja or nazwa")


class FolderZPrzygotowanymiObrazami(models.Model):
    sciezka = models.TextField(default="", blank=True, null=True)
    nazwa = models.TextField(default="", blank=True, null=True)
    sesja = models.ForeignKey("Sesja", on_delete=models.CASCADE, blank=True, null=True)

    def getPath(self):
        if self.sciezka:
            return self.sciezka
        elif self.sesja and self.nazwa:
            return os.path.join(self.sesja.sciezka, self.nazwa)
        else:
            raise AttributeError("Not defined sciezka and sesja or nazwa")


class FoldeZPrzetworzonymiObrazami(models.Model):
    sciezka = models.TextField(default="", blank=True, null=True)
    nazwa = models.TextField(default="", blank=True, null=True)

    def getPath(self):
        if self.sciezka:
            return self.sciezka
        elif self.nazwa:
            return os.path.join(self.sesja.sciezka, self.nazwa)
        else:
            raise AttributeError("Not defined sciezka and nazwa")


class FolderModele(models.Model):
    sciezka = models.TextField(default="", blank=True, null=True)
    nazwa = models.TextField(default="", blank=True, null=True)

    def getPath(self):
        if self.sciezka:
            return self.sciezka
        elif self.nazwa:
            return os.path.join(self.sesja.sciezka, self.nazwa)
        else:
            raise AttributeError("Not defined sciezka and nazwa")


class ObrazPoDostosowaniu(models.Model):
    FLIP_V = 'V'
    FLIP_H = 'H'
    ORGINAL = 'O'
    METHODS = (
        (FLIP_V, "flipped vertical"),
        (FLIP_H, "flipped horizontal"),
        (ORGINAL, "orginal")
    )
    pozycjaCropa = models.OneToOneField("PozycjaCropa", related_name="obraz", on_delete=models.CASCADE)

    klatkaMacierzysta = models.ForeignKey("Klatka", on_delete=models.CASCADE)
    sciezka = models.TextField(default="", blank=True, null=True)
    nazwa = models.TextField(default="", blank=True, null=True)
    metoda = models.CharField(max_length=1, choices=METHODS)
    zlecenie = models.ForeignKey("ZlecenieAugmentacji", on_delete=models.CASCADE, null=True)
    # PozycjaPunktuPoCrop w polu oddzielnym

    def getPath(self):
        if self.sciezka:
            return self.sciezka
        elif self.nazwa:
            return os.path.join(self.zlecenie.folder.getPath(), self.nazwa)
        else:
            raise AttributeError("Not defined sciezka and nazwa")


class ZlecenieAugmentacji(models.Model):
    klatka = models.ForeignKey("Klatka", on_delete=models.CASCADE)
    kodAugmentacji = models.IntegerField(default=114)  # po kolei: flipV(0 or 1), flipH(0 or 1), randomCrop(1-9)
    folder = models.ForeignKey("FolderZPrzygotowanymiObrazami", on_delete=models.CASCADE)
    wTrakcie = models.BooleanField(default=False)


class ZbioryDanych(models.Model):
    sesja = models.ForeignKey("Sesja", on_delete=models.CASCADE)
    uczacy = models.ManyToManyField("ObrazPoDostosowaniu", related_name="zbioryUczacy")
    walidacyjny = models.ManyToManyField("ObrazPoDostosowaniu", related_name="zbioryWalidacyjny", blank=True)
    testowy = models.ManyToManyField("ObrazPoDostosowaniu", related_name="zbioryTestowy", blank=True)
    kolor = models.ForeignKey("Kolor", related_name="zbioryDanych", on_delete=models.CASCADE, blank=True, null=True)


class Sieci(models.Model):
    inputSizeX = models.IntegerField(default=-1)
    inputSizeY = models.IntegerField(default=-1)
    opisJSON = models.TextField(default="")


class ParametryUczenia(models.Model):
    learning_rate = models.FloatField(default=0.0001, blank=True, null=True)
    batch_size = models.IntegerField(default=64, blank=True, null=True)
    dropout = models.FloatField(default=0.5, blank=True, null=True)
    iloscIteracji = models.IntegerField(default=10000, blank=True, null=True)
    saveStep = models.IntegerField(default=500, blank=True, null=True)
    epochSize = models.IntegerField(default=50, blank=True, null=True)
    modelSieci = models.ForeignKey("Sieci", on_delete=models.CASCADE)
    zbiory = models.ForeignKey("ZbioryDanych", on_delete=models.CASCADE, blank=True, null=True)  # deprecated
    opisUczeniaJSON = models.TextField(default="", blank=True)


class AktualneWyniki(models.Model):
    data = models.DateTimeField(default=timezone.now)
    status = models.TextField(default="")


class Uczenie(models.Model):
    STATUS_UCZENIA = (
        ('N', 'do nauczania'),
        ('T', 'w trakcie'),
        ('K', 'ukonczono nauke'),
    )
    statusNauki = models.CharField(max_length=1, choices=STATUS_UCZENIA, default='N')
    opis = models.TextField(blank=True, null=True)
    wynik = models.OneToOneField("WynikUczenia", related_name="learn", blank=True, null=True, on_delete=models.CASCADE)
    parametry = models.ForeignKey("ParametryUczenia", on_delete=models.CASCADE)
    zbiory = models.ForeignKey("ZbioryDanych", on_delete=models.CASCADE, blank=True, null=True)


class WynikUczenia(models.Model):
    model_file = models.TextField()
    mean = models.FloatField(default=0.0, blank=True, null=True)
    std = models.FloatField(default=0.0, blank=True, null=True)
    max = models.FloatField(default=0.0, blank=True, null=True)
    errors = models.TextField(default="", blank=True, null=True)
    min_mean_during_learning = models.FloatField(default=0.0, blank=True, null=True)
    histogram = models.ImageField(blank=True, null=True)


class FilmWynik(models.Model):
    wynikUczenia = models.ForeignKey("WynikUczenia", on_delete=models.CASCADE)
    film = models.OneToOneField("Film", on_delete=models.CASCADE)
    sciezka = models.TextField()


class WynikPrzetwarzania(models.Model):
    wspolrzednaX = models.FloatField()
    wspolrzednaY = models.FloatField()
    klatka = models.OneToOneField("Klatka", on_delete=models.CASCADE)
    numer = models.IntegerField(default=0)
    nazwa = models.CharField("nazwa", max_length=80, default="")


class Sesja(models.Model):
    folderZObrazami = models.OneToOneField("FolderZObrazami", on_delete=models.CASCADE)
    filmyPrzetworzone = models.ManyToManyField("Film", related_name="sesjaPrzetworzone", blank=True)
    filmyUzytkownik = models.ManyToManyField("Film", related_name="sesjaUzytkownika", blank=True)
    folderPrzetworzone = models.OneToOneField("FoldeZPrzetworzonymiObrazami", on_delete=models.CASCADE, blank=True,
                                              null=True)

    folderModele = models.OneToOneField("FolderModele", on_delete=models.CASCADE, blank=True, null=True)
    data = models.DateTimeField(default=timezone.now)
    nazwa = models.TextField(default="Nienazwana_{}".format(timezone.now()))
    ostatniaAktualizacja = models.DateTimeField(default=timezone.now)
    sciezka = models.TextField(default="", blank=True, null=True)
    zbiorKolorow = models.ForeignKey(
        "ZbiorKolorow", on_delete=models.deletion.PROTECT
    )
