from django.db import models
from django.utils import timezone


class Status(models.Model):
    status = models.CharField("status", max_length=100)

    class Meta:
        abstract = True


class StatusFilmu(Status):
    pass


class StatusPozycji(Status):
    pass


class StatusPozycjiCrop(Status):
    pass


class Punkt(models.Model):
    pozycjaX = models.IntegerField("x", default=0)
    pozycjaY = models.IntegerField("y", default=0)

    class Meta:
        abstract = True


class PozycjaPunktu(Punkt):
    klatka = models.ForeignKey("Klatka", related_name="pozycja", on_delete=models.CASCADE)
    status = models.ForeignKey("StatusPozycji", related_name="pozycja", on_delete=models.CASCADE, blank=True, null=True)


class PozycjaPunktuPoCrop(Punkt):
    obraz = models.ForeignKey("ObrazPoDostosowaniu", related_name="pozycja", on_delete=models.CASCADE)
    status = models.ForeignKey("StatusPozycjiCrop", related_name="pozycja", on_delete=models.CASCADE, blank=True,
                               null=True)


class PozycjaCropa(Punkt):
    pass


class Klatka(models.Model):
    film = models.ForeignKey("Film", related_name="film", on_delete=models.CASCADE)
    nr = models.IntegerField(default=0)
    sciezka = models.TextField(default="")
    data = models.DateTimeField(default=timezone.now)


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
    sciezka = models.TextField(default="")


class FolderZPrzygotowanymiObrazami(models.Model):
    sciezka = models.TextField(default="")


class ObrazPoDostosowaniu(models.Model):
    FLIP_V = 'V'
    FLIP_H = 'H'
    ORGINAL = 'O'
    METHODS = (
        (FLIP_V, "flipped vertical"),
        (FLIP_H, "flipped horizontal"),
        (ORGINAL, "orginal")
    )
    # zostaje, ale prawdopodobnie najlepiej liczyc pozycje punktu na podstawie odpowidnika przypoisanego ( delta = punktPoCrop - PoUczeniu, PunktNaKlatce = punktPierwotny - delta (+ uwzględnić metodę i resize))
    pozycjaCropa = models.OneToOneField("PozycjaCropa", related_name="obraz", on_delete=models.CASCADE)

    wspResize = models.FloatField(default=1.0)
    klatkaMacierzysta = models.ForeignKey("Klatka", on_delete=models.CASCADE)
    sciezka = models.TextField(default="")
    metoda = models.CharField(max_length=1, choices=METHODS)
    # PozycjaPunktuPoCrop w polu oddzielnym


class ZlecenieAugmentacji(models.Model):
    klatka = models.ForeignKey("Klatka", on_delete=models.CASCADE)
    kodAugmentacji = models.IntegerField(default=114)  # po koleji: flipV(0 or 1), flipH(0 or 1), randomCrop(1-9)
    folder = models.OneToOneField("FolderZPrzygotowanymiObrazami", on_delete=models.CASCADE)
    oczekiwanyRozmiarX = models.IntegerField("x")
    oczekiwanyRozmiarY = models.IntegerField("y")
    wTrakcie = models.BooleanField(default=False)


# Konieć CZ1:

class ZbioryDanych(models.Model):
    sesja = models.ForeignKey("Sesja", on_delete=models.CASCADE)
    uczacy = models.ManyToManyField("Klatka", related_name="zbioryUczacy")
    walidacyjny = models.ManyToManyField("Klatka", related_name="zbioryWalidacyjny", blank=True)
    testowy = models.ManyToManyField("Klatka", related_name="zbioryTestowy", blank=True)


class Sieci(models.Model):
    opisXML = models.TextField(default="")


class ParametryUczenia(models.Model):
    learning_rate = models.FloatField(default=0.0001, blank=True, null=True)
    batch_size = models.IntegerField(default=64, blank=True, null=True)
    dropout = models.FloatField(default=0.5, blank=True, null=True)
    iloscIteracji = models.IntegerField(default=10000, blank=True, null=True)
    modelSieci = models.ForeignKey("Sieci", on_delete=models.CASCADE)
    zbiory = models.ForeignKey("ZbioryDanych", on_delete=models.CASCADE)
    opisUczeniaXML = models.TextField(default="")


class AktualneWyniki(
    models.Model):  # używane przez CRONa głównego backendu do śledzenia uczenia sieci bez potrzeby kounikacji
    data = models.DateTimeField(default=timezone.now)
    status = models.TextField(default="")


class Uczenie(
    models.Model):  # na tej podstawie CRON backendu machinelearning rozpoznaje kiedy się uczyć i jak (z danych i parsowania xml)

    STATUS_UCZENIA = (
        ('N', 'do nauczania'),
        ('K', 'ukonczono nauke'),
    )
    statusNauki = models.CharField(max_length=1, choices=STATUS_UCZENIA, default='N')
    opis = models.TextField(blank=True, null=True)
    wynik = models.OneToOneField("WynikUczenia", blank=True, null=True, on_delete=models.CASCADE)
    parametry = models.ForeignKey("ParametryUczenia", on_delete=models.CASCADE)


class WynikUczenia(models.Model):
    sciezkaDoSieci = models.TextField()
    mean = models.FloatField(default=0.0, blank=True, null=True)
    std = models.FloatField(default=0.0, blank=True, null=True)
    minMeanWTrakcieNauki = models.FloatField(default=0.0, blank=True, null=True)
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


# koniecCZ2

class Sesja(models.Model):
    folderZObrazami = models.OneToOneField("FolderZObrazami", on_delete=models.CASCADE)
    filmyPrzetworzone = models.ManyToManyField("Film", related_name="sesjaPrzetworzone", blank=True)
    filmyUzytkownik = models.ManyToManyField("Film", related_name="sesjaUzytkownika", blank=True)
    data = models.DateTimeField(default=timezone.now)
    nazwa = models.TextField(default="Nienazwana_{}".format(timezone.now()))
    ostatniaAktualizacja = models.DateTimeField(default=timezone.now)
