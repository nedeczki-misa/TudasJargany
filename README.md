# TudasJargany

Egyszerű, színes Python/Tkinter játék gyerekeknek.

## A játék menete

1. Fogd meg az alkatrészeket az egér bal gombjával.
2. Az **AUTÓ SZÍNE** táblán válassz a 16 szín közül. A szín építés közben is megváltoztatható.
3. A felső **AUTÓFORMA** menüben válassz városi autót, sportautót, terepjárót vagy pickupot.
4. Húzd az alkatrészeket az azonos alakú, szaggatott helyükre. A kerekek, lámpa és lökhárító mellett külön légterelőt és vonóhorgot is fel lehet szerelni.
5. Ha minden kötelező elem a helyén van, kattints az **INDULÁS!** gombra.
6. Az utcán gyűjtsd össze a csillagokat, és kerüld ki az akadályokat.
7. A műhely alsó sávjában kattints a **FELADATOK** gombra. A Matek alapból be van jelölve, az Angol kikapcsolva. Jelöld be az Angolt is, ha vegyes feladatokat szeretnél.
8. Ha az autó akadálynak ütközik, megnyílik a **Tudás-szerviz**. Minden kérdésre 60 másodperc áll rendelkezésre. Helyes válasz után élet- és csillagváltozás nélkül folytatódik a vezetés.

A Matek alapértelmezett feladatként összeadást és kivonást gyakoroltat a 30-as számkörben. Ha az Angol is be van jelölve, alap angol–magyar szavak is érkeznek, például `apple` = alma vagy kutya = `dog`; ekkor a két tantárgy felváltva jelenik meg.

Angolfeladatnál húzd az egeret az angol szó fölé: a játék offline kimondja a Windows telepített angol beszédhangjával. A kiejtéshez Windows és legalább egy angol rendszerhang szükséges.

## Bónuszok és nehezedés

- Minden 10. csillag után külön bónusz tanulási feladat következik, amely 2 csillagot ér.
- Minden 10. csillagnál egy fokozattal gyorsabb lesz az autó, és ekkor jelenik meg a bónuszfeladat is.
- A pálya gyorsulását az `assets/sounds/speed_up.wav` hang jelzi.
- Minden 30. pontnál külön, 60 másodperces tanulási feladat jelenik meg. Helyes válasszal egy élet tölthető vissza, legfeljebb háromig; ezen a mérföldkőn a szokásos +2 csillagos bónusz nem jár.
- Ütközéskor fékhang, majd bójánál könnyű, más járműnél vagy sávlezárásnál erősebb ütközési hang hallható.
- A bóják, más autók és buszok mellett vadmotorosok is megjelennek; a motorosok cikázva sávot váltanak.
- Induláskor motorhang szól; vezetés közben a **DUDÁLJ** gomb a kürtöt használja. Felszerelt rendőrségi szirénánál szirénahang is szól.
- A lezárt sávba hajtás után három egymást követő, a műhelyben kiválasztott tantárgyakból érkező feladatot kell megoldani.
- Az út négysávos; az egérrel mind a négy sáv közvetlenül kiválasztható.
- Ütközési feladatnál a hibás válasz vagy az idő lejárta egy életet elvesz, a helyes válasz viszont nem kerül életbe és nem ad csillagot.
- A 10 csillagos bónuszfeladat helyes válasza továbbra is 2 csillagot ér; időtúllépéskor a bónusz elvész.

Vezetni a képernyő alján lévő **BALRA** és **JOBBRA** gombbal, az út megfelelő sávjára kattintva, illetve a bal és jobb nyílbillentyűvel lehet.

A **KÖTELEZŐK ÖSSZERAKÁSA** gomb a még hiányzó kötelező alkatrészeket egymás után a helyükre pattintja. Az extrák – a vonóhorog, a légterelő, a rendőrségi sziréna és a taxijel – választhatók, nélkülük is el lehet indulni. Csak a ténylegesen felszerelt extrák jelennek meg vezetés közben. Az alkatrészek húzás közben sem mozgathatók ki a látható játéktérből, és kisebb ablaknál is a tálcán belül maradnak.

## Indítás

Windows alatt kattints duplán a `start.bat` fájlra, vagy terminálból futtasd:

```powershell
python main.py
```

Nincs szükség külső csomagra; a játék a Python beépített Tkinter felületét használja.
