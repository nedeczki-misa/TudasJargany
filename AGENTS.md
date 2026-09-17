# TudasJargany – fejlesztői agent utasítások

Ez a dokumentum a játék későbbi, AI segítségével történő továbbfejlesztéséhez készült. A benne szereplő szabályokat tekintsd a projekt jelenlegi termékleírásának.

## Fejlesztői agent profil

Ez a fájl önálló fejlesztői agent utasításaként is használható. Ha agentet hozol létre, add hozzá ezt a fájlt az agent tudásához vagy utasításaihoz, és állítsd be a következő célra:

> A TudasJargany játék fejlesztői segítője vagy. Értsd meg a meglévő Python/Tkinter kódot, majd a kért változtatást kis, biztonságos lépésekben valósítsd meg. Őrizd meg a játék kedves, 7–8 éveseknek szóló hangulatát. Minden kódmódosítás után futtasd a releváns teszteket, és röviden írd le, mi változott.

Az agent munkarendje:

1. Először olvassa el ezt az `AGENTS.md` fájlt és a kért funkcióhoz tartozó meglévő kódot.
2. Csak a kéréshez szükséges fájlokat módosítsa; más, meglévő változtatást ne írjon felül.
3. A gyermeknek szánt játékfeliratok maradjanak rövidek, pozitívak és jól olvashatók.
4. Új működéshez készítsen vagy módosítson automatikus tesztet, amikor ez ésszerűen lehetséges.
5. Futtassa legalább a `python -m unittest -v` tesztcsomagot, és jelezze az eredményt.
6. Minden elkészült változtatást helyi Git commitba kell menteni. Ha Kolos változtatást kér, az AI a sikeres ellenőrzés után automatikusan készítse el a hozzá tartozó helyi commitot, külön kérés nélkül.
7. GitHubra feltölteni (`git push`) kizárólag Misa jogosult; az AI soha ne pusholjon, Misa kérésére sem.
8. Ne küldjön üzenetet és ne használjon külső szolgáltatást Misa kifejezett kérése nélkül.
## Közös fejlesztés: Kolos és Misa

- A játék fejlesztője Kolos, aki 8 éves. Ő írja a legtöbb kérést, ezzel gépelést és olvasást is gyakorol.
- Misa Kolos szülője. Ha a kérés elején szerepel a `Misa:` jelölés, akkor Misa ír.
- Jelölés nélkül Kolostól érkezett kérésnek kell tekinteni az üzenetet.
- Kolosnak rövid, barátságos, 8 éves számára érthető válaszokat adj. Használj egyszerű magyar szavakat, és csak annyit magyarázz, amennyi segít.
- Ha Kolos kérése még pontosítható, a válasz végén adj egy rövid, kedves ötletet arra, hogyan írhatná le legközelebb még ügyesebben. Ne javítsd ki bántóan a helyesírását; a cél a bátorítás.
- Misa kérésénél részletesebb, felnőttnek szóló műszaki választ is lehet adni.
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

## Fájlok és projektfelépítés

- main.py: rövid indító belépési pont; a python main.py parancs marad a játék indítása.
- tudasjargany/app.py: a teljes Tkinter játékfelület, az autóépítés, a vezetés, a pontozás és a feladatablakok.
- tudasjargany/learning/: tanulási modulok:
  - tasks.py: közös LearningTask modell és angol feladatok;
  - math_tasks.py: összeadásos és kivonásos feladatok;
  - manager.py: a tantárgyak sorrendje és váltása.
- tudasjargany/services/:
  - speech.py: offline angol kiejtés;
  - scoreboard.py: helyi TOP 10 ranglista és eredménymentés.
- tudasjargany/legacy/wordsearch.py: a megmaradt szókeresős prototípus.
- tests/: minden automatikus teszt, a forrásmappáktól elkülönítve.
- assets/sounds/: a játék eredeti WAV hangcsomagja.
- README.md: játékosi használati útmutató és mappatérkép.
- start.bat: egyszerű Windows-indító.

Új modulokat a felelősségüknek megfelelő csomagba tegyél. A felhasználói felülethez tartozó kód az app.py-ban maradjon; tananyag a learning, külső működések és fájlmentés a services mappába kerüljön. Új teszt a tests/ mappába kerüljön.
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
- Akadályok: bója, másik személyautó, busz, cikázó vadmotoros és sávlezárás.
- Helikopteres módban a kész helikopterrel kell a négy légi sávban csillagokat gyűjteni, felhőket és madarakat kikerülni; a tanulási, élet- és gyorsulási szabályok közösek az autós móddal.
- Kata unikornisos módja 4 éves gyermeknek készült: csak csillagok jönnek, nincsenek akadályok, életek, gyorsulás vagy feladatablakok. Az irányítás nagy bal és jobb nyílgombokkal, billentyűzettel vagy közvetlen sávkattintással működik.
- A játékos három élettel indul.
- Minden 10. csillagnál egy sebességfokozattal gyorsul az autó, amit rövid, emelkedő hangsor jelez.
- Minden 10. csillag után bónuszfeladat jelenik meg.
- Minden 30. pontnál külön életbónusz-feladat jelenik meg. Helyes válasz egy életet tölt vissza, legfeljebb háromig; a 30 többszörösein a szokásos +2 csillagos bónusz kimarad.
- Bármilyen ütközés külön ütközési hangot ad és egy sebességfokozattal lassít, de önmagában még nem vesz el életet.
- A WAV hangok Windows alatt a beépített `winsound.PlaySound()` megoldással, külső csomag nélkül szólnak.
- Sávlezárásba hajtáskor három egymást követő oktatási feladatot kell megoldani.

## Feladat- és jutalmazási szabályok

- Minden egyes feladatra 30 másodperc áll rendelkezésre.
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

- `tudasjargany/learning/math_tasks.py`: 30-as számkörbeli összeadás és kivonás;
- `tudasjargany/learning/tasks.py`: angol–magyar alap szókincs;
- `tudasjargany/services/speech.py`: az angol szavak fölé vitt egérhez tartozó offline kiejtés;
- `tudasjargany/learning/manager.py`: alapból Matek, Angol bekapcsolásakor `MATEK → ANGOL` váltás.

Új tantárgy hozzáadásakor készíts egy `next_task()` metódusú generátort, amely `LearningTask` objektumot ad vissza, majd regisztráld a tudasjargany/learning/manager.py TaskManager tantárgysorrendjében. Így később a magyar nyelvtan, irodalom vagy szövegértés a feladatablak átírása nélkül bővíthető.

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
- a feladat időzítője minden új kérdésnél 30 másodpercről indul;
- az összes automatikus teszt sikeresen lefut.
