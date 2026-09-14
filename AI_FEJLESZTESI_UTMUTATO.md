# TudasJargany – AI fejlesztési útmutató

Ez a dokumentum a játék későbbi, AI segítségével történő továbbfejlesztéséhez készült. A benne szereplő szabályokat tekintsd a projekt jelenlegi termékleírásának.

## Alapkoncepció

- Végleges név: **TudasJargany**
- Szlogen: **Építs, vezess, tanulj!**
- Célcsoport: elsősorban 2. osztályos, körülbelül 7–8 éves gyerekek.
- A játékos építőkockákból összeállít egy autót, majd négysávos úton vezet vele.
- A vezetés és az oktatási feladatok egy közös jutalmazási rendszerhez kapcsolódnak.
- A játék később ne csak matematikát, hanem magyar nyelvet, nyelvtant, olvasást, irodalmat és más 2. osztályos tananyagot is gyakoroltasson.

## Jelenlegi technológia és indítás

- Python 3 és a beépített Tkinter grafikus felület.
- Nincs külső csomag vagy internetkapcsolat szükséglet.
- Indítás: `python main.py`, Windows alatt a `start.bat` fájl is használható.
- Tesztek: `python -m unittest -v`.
- A magyar szövegeket és fájlokat UTF-8 kódolással kell megőrizni.

## Fájlok

- `main.py`: a teljes felület, az autóépítés, a vezetés, az akadályok, a pontozás és a feladatablakok.
- `math_tasks.py`: összeadásos és kivonásos feladatok generátora.
- `learning_tasks.py`: közös `LearningTask` feladatmodell és angol szókincsgenerátor.
- `task_manager.py`: a műhelyben kiválasztott tantárgyak sorrendjét és váltását kezeli.
- `speech.py`: Windows `System.Speech` alapú, offline angol kiejtés egér-ráhúzásra.
- `test_learning_tasks.py`: angol és többtantárgyas feladatok automatikus tesztjei.
- `test_math_tasks.py`: a feladatgenerátor automatikus tesztjei.
- `README.md`: játékosi használati útmutató.
- `start.bat`: egyszerű Windows-indító.
- `wordsearch.py` és `test_wordsearch.py`: a projekt korábbi szókeresős prototípusának megmaradt fájljai; a jelenlegi autós játék nem használja őket.

## Autóépítés

### Kötelező elemek

Az autó csak ezek felszerelése után indulhat el:

1. autóalap;
2. tető/kabin;
3. lámpa;
4. lökhárító;
5. bal kerék;
6. jobb kerék.

### Választható extrák

- vonóhorog;
- hátsó légterelő;
- rendőrségi sziréna;
- taxijel.

Az extrák nélkül is el lehet indulni. Vezetés közben csak a ténylegesen felszerelt extrák jelenjenek meg. A **Kötelezők összerakása** gomb automatikusan csak a kötelező elemeket szereli fel; az extrákról a játékos dönt.

### Testreszabás

- 16 választható autószín van egy 4×4-es palettán.
- Formák: városi autó, sportautó, terepjáró és pickup.
- A kiválasztott szín és forma az építőnézetben és vezetés közben is maradjon azonos.
- Az alkatrészek egérrel húzhatók, a megfelelő hely közelében automatikusan bepattannak.
- Az elemek kis ablakméretnél és húzás közben sem kerülhetnek a látható területen kívülre.

## Vezetés

- Az út négysávos.
- Irányítás: képernyőgombok, bal/jobb nyílbillentyű, `A`/`D`, illetve közvetlen kattintás egy sávra.
- Gyűjthető elem: csillag.
- Akadályok: bója, másik személyautó, busz és sávlezárás.
- A játékos három élettel indul.
- Minden 10. csillagnál egy sebességfokozattal gyorsul az autó, amit rövid, emelkedő hangsor jelez.
- Minden 10. csillag után bónuszfeladat jelenik meg.
- Minden 30. pontnál külön életbónusz-feladat jelenik meg. Helyes válasz egy életet tölt vissza, legfeljebb háromig; a 30 többszörösein a szokásos +2 csillagos bónusz kimarad.
- Bármilyen ütközés külön ütközési hangot ad és egy sebességfokozattal lassít, de önmagában még nem vesz el életet.
- Sávlezárásba hajtáskor három egymást követő oktatási feladatot kell megoldani.

## Feladat- és jutalmazási szabályok

- Minden egyes feladatra 60 másodperc áll rendelkezésre.
- A műhely Feladatok menüjében alapból csak a Matek aktív; Angol bekapcsolásakor a kiválasztott tantárgyak felváltva érkeznek.
- Az utolsó 10 másodpercben a visszaszámláló piros.
- Ütközéshez tartozó helyes válasz: nincs életvesztés, és nem jár csillag.
- Ütközéshez tartozó hibás válasz: egy élet levonása, majd újrapróbálható a feladat, ha maradt élet.
- Ütközési feladat időtúllépése: egy élet levonása.
- A 10 csillagos bónuszfeladat helyes válasza: +2 csillag.
- Bónuszfeladat időtúllépése: nem jár extra csillag és nem kell életet levonni.
- Az egymást követő feladatok ne ismétlődjenek; a matematikai generátor jelenleg az utolsó 12 kérdést megjegyzi.

## Jelenlegi matematika

- Összeadás és kivonás a 30-as számkörben.
- Minden számnak, részeredménynek és eredménynek 0 és 30 között kell maradnia.
- Lehetséges feladattípusok:
  - hiányzó eredmény: `14 + 9 = ?`;
  - hiányzó bal oldali szám: `? − 7 = 12`;
  - hiányzó jobb oldali szám: `18 − ? = 11`;
  - hiányzó műveleti jel: `8 ? 6 = 14`.
- A válaszokat nagy, egérrel kattintható gombokkal kell megadni.

## Többtantárgyas feladatrendszer

A feladatablak a közös `LearningTask` modellt használja, ezért nem függ közvetlenül a matematikai generátortól:

```python
@dataclass(frozen=True)
class LearningTask:
    prompt: str
    answer: str
    choices: tuple[str, ...]
    explanation: str
    subject: str
```

A jelenlegi modulok:

- `math_tasks.py`: 30-as számkörbeli összeadás és kivonás;
- `learning_tasks.py`: angol–magyar alap szókincs;
- `speech.py`: az angol szavak fölé vitt egérhez tartozó offline kiejtés;
- `task_manager.py`: alapból Matek, Angol bekapcsolásakor `MATEK → ANGOL` váltás.

Új tantárgy hozzáadásakor készíts egy `next_task()` metódusú generátort, amely `LearningTask` objektumot ad vissza, majd regisztráld a `TaskManager` tantárgysorrendjében. Így később a magyar nyelvtan, irodalom vagy szövegértés a feladatablak átírása nélkül bővíthető.

## Lehetséges 2. osztályos feladattípusok – a konkrét tananyagot pedagógussal érdemes ellenőrizni:

- szótagolás és szótagszám;
- magánhangzó/mássalhangzó felismerése;
- rövid és hosszú magánhangzók;
- ábécérend;
- `j` vagy `ly` kiválasztása;
- mondatvégi írásjel;
- szavak mondattá rendezése;
- főnév és ige egyszerű felismerése;
- rövid szöveg utáni szövegértési kérdés;
- mese eseményeinek sorrendbe rakása;
- szereplő, helyszín vagy rím felismerése.

## Ajánlott következő fejlesztési lépések

1. Egységes kezdőképernyő és arculat kialakítása a **TudasJargany** névhez.
2. A műhely Feladatok menüjének bővítése új tantárgyak jelölőnégyzeteivel.
3. Angol szókincs bővítése témakörök szerint (állatok, színek, család, iskola).
4. Magyar és olvasási feladatgenerátor beillesztése a `TaskManager` váltási sorrendjébe.
5. Tantárgyválasztó beállítás készítése: vegyes, csak matematika, csak angol vagy későbbi tantárgyak.
6. Nehézségi szintek és szülői/pedagógusi beállítások.
7. Eredmények mentése helyben: gyakorolt témák, helyes válaszok, gyakori hibák.

## Fejlesztési alapelvek

- A célcsoport miatt a szöveg legyen rövid, barátságos és jól olvasható.
- Az elsődleges vezérlés egérrel működjön; billentyűzet csak kiegészítés legyen.
- Ne legyen negatív vagy megszégyenítő visszajelzés. Hibánál rövid magyarázat és újrapróbálás járjon.
- Az oktatási feladat megjelenésekor a vezetés teljesen álljon meg.
- A feladatoknak egyértelműen csak egy helyes válaszuk legyen.
- Minden új feladatgenerátor kapjon automatikus teszteket a válasz, a tartomány, az egyértelműség és az ismétlődés ellenőrzésére.
- A meglévő 900×650-es minimum ablakméretet és a képernyőn belüli elrendezést meg kell őrizni.
- Külső függőség csak akkor kerüljön be, ha valóban szükséges, és az indítási útmutatót is frissíteni kell.

## Késznek tekintési ellenőrzőlista

Egy későbbi módosítás akkor kész, ha:

- a program `python main.py` paranccsal elindul;
- az autó kötelező elemekkel, extrák nélkül is elindítható;
- minden kiválasztott szín, forma és extra helyesen jelenik meg az úton;
- mind a négy sáv elérhető egérrel és billentyűzettel;
- a 10 pontos gyorsulás, a nem 30-as mérföldkövek bónuszfeladata és a 30 pontos életbónusz-feladat működik;
- ütközéskor a sebesség visszaesik, élet pedig csak hibás válasznál vagy időtúllépésnél fogy;
- a feladat időzítője minden új kérdésnél 60 másodpercről indul;
- az összes automatikus teszt sikeresen lefut.
