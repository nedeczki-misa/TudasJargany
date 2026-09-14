# TudasJargany

Egyszerű, színes Python/Tkinter játék gyerekeknek.

## A játék menete

1. Fogd meg az alkatrészeket az egér bal gombjával.
2. Az **AUTÓ SZÍNE** táblán válassz a 16 szín közül. A szín építés közben is megváltoztatható.
3. A felső **AUTÓFORMA** menüben válassz városi autót, sportautót, terepjárót vagy pickupot.
4. Húzd az alkatrészeket az azonos alakú, szaggatott helyükre. A kerekek, lámpa és lökhárító mellett külön légterelőt és vonóhorgot is fel lehet szerelni.
5. Ha minden kötelező elem a helyén van, kattints az **INDULÁS!** gombra.
6. Az utcán gyűjtsd össze a csillagokat, és kerüld ki az akadályokat.
7. Ha az autó akadálynak ütközik, megnyílik a **Matek-szerviz**. Minden feladatra 60 másodperc áll rendelkezésre. Helyes válasz után élet- és csillagváltozás nélkül folytatódik a vezetés.

A matematikai feladatok összeadást és kivonást gyakoroltatnak a 30-as számkörben. Változó helyen hiányozhat az eredmény, az egyik szám vagy a `+`/`−` műveleti jel. Az egymást követő ütközéseknél mindig más feladat jelenik meg.

## Bónuszok és nehezedés

- Minden 10. csillag után külön bónusz matekfeladat következik, amely 2 csillagot ér.
- Minden 10. csillagnál egy fokozattal gyorsabb lesz az autó, és ekkor jelenik meg a bónuszfeladat is.
- Minden 30. pontnál külön, 60 másodperces matekfeladat jelenik meg. Helyes válasszal egy élet tölthető vissza, legfeljebb háromig; ezen a mérföldkőn a szokásos +2 csillagos bónusz nem jár.
- Ütközéskor a sebesség egy fokozattal visszaáll.
- A bóják mellett más autók és buszok is közlekednek az úton.
- A lezárt sávba hajtás után három egymást követő matekfeladatot kell megoldani.
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
