"""Mod texts in every language the game ships. Wording follows each language's vanilla "Raze" option."""

# Game language codes, as in data/local_<code>.pack. English is the main pack's default.
LANGUAGES = ("en", "ru", "ge", "fr", "it", "sp", "pl", "cz", "tr", "br", "kr", "cn", "zh")
FIELDS = ("title", "description", "bundle_title", "bundle_description", "effect_description")

TEXTS = {
    "en": {
        "title": "Raze Forever",
        "description": "Wipe the settlement off the map so that no one can ever occupy it again. This cannot be undone.",
        "bundle_title": "Erased Forever",
        "bundle_description": "These ruins have been destroyed for good. No one will ever settle here again.",
        "effect_description": "Ruins erased forever: this region cannot be occupied or colonised",
    },
    "ru": {
        "title": "Стереть навсегда",
        "description": "Сравнять поселение с землёй так, что его больше никто и никогда не сможет занять. Это необратимо.",
        "bundle_title": "Стёрто навсегда",
        "bundle_description": "Эти руины уничтожены окончательно. Здесь больше никто не сможет поселиться.",
        "effect_description": "Руины стёрты навсегда: регион нельзя занять или заселить",
    },
    "ge": {
        "title": "Für immer niederreißen",
        "description": "Die Siedlung wird ausgelöscht, sodass niemand sie je wieder besetzen kann. Dies kann nicht rückgängig gemacht werden.",
        "bundle_title": "Für immer ausgelöscht",
        "bundle_description": "Diese Ruinen wurden endgültig zerstört. Niemand wird sich hier je wieder niederlassen.",
        "effect_description": "Für immer ausgelöschte Ruinen: Diese Region kann weder besetzt noch kolonisiert werden",
    },
    "fr": {
        "title": "Raser à jamais",
        "description": "La colonie est rayée de la carte : plus personne ne pourra jamais l'occuper. Cette action est irréversible.",
        "bundle_title": "Effacée à jamais",
        "bundle_description": "Ces ruines ont été détruites pour de bon. Plus personne ne s'installera jamais ici.",
        "effect_description": "Ruines effacées à jamais : cette région ne peut être ni occupée ni colonisée",
    },
    "it": {
        "title": "Radi al suolo per sempre",
        "description": "L'insediamento viene cancellato dalla mappa: nessuno potrà mai più occuparlo. L'azione è irreversibile.",
        "bundle_title": "Cancellato per sempre",
        "bundle_description": "Queste rovine sono state distrutte per sempre. Nessuno potrà mai più stabilirsi qui.",
        "effect_description": "Rovine cancellate per sempre: questa regione non può essere occupata né colonizzata",
    },
    "sp": {
        "title": "Arrasar para siempre",
        "description": "El asentamiento desaparece del mapa y nadie podrá volver a ocuparlo jamás. Esta acción es irreversible.",
        "bundle_title": "Borrado para siempre",
        "bundle_description": "Estas ruinas han sido destruidas para siempre. Nadie volverá a asentarse aquí.",
        "effect_description": "Ruinas borradas para siempre: esta región no puede ocuparse ni colonizarse",
    },
    "pl": {
        "title": "Zniszczenie na zawsze",
        "description": "Osada zostaje starta z powierzchni ziemi i nikt już nigdy nie będzie mógł jej zająć. Tej decyzji nie można cofnąć.",
        "bundle_title": "Starte na zawsze",
        "bundle_description": "Te ruiny zostały zniszczone na zawsze. Nikt już nigdy się tu nie osiedli.",
        "effect_description": "Ruiny starte na zawsze: tego regionu nie można zająć ani skolonizować",
    },
    "cz": {
        "title": "Srovnat se zemí navždy",
        "description": "Sídlo zmizí z mapy a už nikdy ho nikdo nebude moci obsadit. Tuto akci nelze vrátit.",
        "bundle_title": "Navždy vymazáno",
        "bundle_description": "Tyto rozvaliny byly zničeny navždy. Nikdo se zde už nikdy neusadí.",
        "effect_description": "Navždy vymazané rozvaliny: tuto oblast nelze obsadit ani kolonizovat",
    },
    "tr": {
        "title": "Sonsuza Dek Yerle Bir Et",
        "description": "Yerleşim yeri haritadan silinir ve bir daha asla kimse tarafından işgal edilemez. Bu işlem geri alınamaz.",
        "bundle_title": "Sonsuza Dek Silindi",
        "bundle_description": "Bu harabeler kalıcı olarak yok edildi. Burada bir daha kimse yerleşemez.",
        "effect_description": "Sonsuza dek silinmiş harabeler: bu bölge işgal edilemez veya kolonileştirilemez",
    },
    "br": {
        "title": "Devastar para sempre",
        "description": "O povoado é apagado do mapa e ninguém jamais poderá ocupá-lo novamente. Esta ação é irreversível.",
        "bundle_title": "Apagado para sempre",
        "bundle_description": "Estas ruínas foram destruídas para sempre. Ninguém jamais se estabelecerá aqui novamente.",
        "effect_description": "Ruínas apagadas para sempre: esta região não pode ser ocupada nem colonizada",
    },
    "kr": {
        "title": "영구 파괴",
        "description": "정착지를 지도에서 지워 다시는 누구도 점령할 수 없게 합니다. 이 결정은 되돌릴 수 없습니다.",
        "bundle_title": "영원히 소멸됨",
        "bundle_description": "이 폐허는 영원히 파괴되었습니다. 다시는 누구도 이곳에 정착할 수 없습니다.",
        "effect_description": "영원히 소멸된 폐허: 이 지역은 점령하거나 식민화할 수 없습니다",
    },
    "cn": {
        "title": "永久毁灭",
        "description": "将该城镇从地图上彻底抹去，任何人都无法再占领此地。此操作无法撤销。",
        "bundle_title": "永久抹除",
        "bundle_description": "这些废墟已被永久摧毁，再也没有人能在此定居。",
        "effect_description": "永久抹除的废墟：此地区无法被占领或殖民",
    },
    "zh": {
        "title": "永久摧毀",
        "description": "將該城鎮從地圖上徹底抹除，任何人都無法再佔領此地。此操作無法復原。",
        "bundle_title": "永久抹除",
        "bundle_description": "這片廢墟已被永久摧毀，再也沒有人能在此定居。",
        "effect_description": "永久抹除的廢墟：此地區無法被佔領或殖民",
    },
}
