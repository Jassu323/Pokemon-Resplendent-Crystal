; Relative to page one; zero denotes an absent later page.
PokedexDescriptionPageOffsets:
ASSERT TreeckoPokedexEntry.page2 - TreeckoPokedexEntry.page1 > 0 && TreeckoPokedexEntry.page2 - TreeckoPokedexEntry.page1 <= 255
ASSERT TreeckoPokedexEntry.page3 - TreeckoPokedexEntry.page1 > 0 && TreeckoPokedexEntry.page3 - TreeckoPokedexEntry.page1 <= 255
ASSERT TreeckoPokedexEntry.page4 - TreeckoPokedexEntry.page1 > 0 && TreeckoPokedexEntry.page4 - TreeckoPokedexEntry.page1 <= 255
	db TreeckoPokedexEntry.page2 - TreeckoPokedexEntry.page1, TreeckoPokedexEntry.page3 - TreeckoPokedexEntry.page1, TreeckoPokedexEntry.page4 - TreeckoPokedexEntry.page1
ASSERT GrovylePokedexEntry.page2 - GrovylePokedexEntry.page1 > 0 && GrovylePokedexEntry.page2 - GrovylePokedexEntry.page1 <= 255
ASSERT GrovylePokedexEntry.page3 - GrovylePokedexEntry.page1 > 0 && GrovylePokedexEntry.page3 - GrovylePokedexEntry.page1 <= 255
	db GrovylePokedexEntry.page2 - GrovylePokedexEntry.page1, GrovylePokedexEntry.page3 - GrovylePokedexEntry.page1, 0
ASSERT SceptilePokedexEntry.page2 - SceptilePokedexEntry.page1 > 0 && SceptilePokedexEntry.page2 - SceptilePokedexEntry.page1 <= 255
ASSERT SceptilePokedexEntry.page3 - SceptilePokedexEntry.page1 > 0 && SceptilePokedexEntry.page3 - SceptilePokedexEntry.page1 <= 255
ASSERT SceptilePokedexEntry.page4 - SceptilePokedexEntry.page1 > 0 && SceptilePokedexEntry.page4 - SceptilePokedexEntry.page1 <= 255
	db SceptilePokedexEntry.page2 - SceptilePokedexEntry.page1, SceptilePokedexEntry.page3 - SceptilePokedexEntry.page1, SceptilePokedexEntry.page4 - SceptilePokedexEntry.page1
ASSERT TorchicPokedexEntry.page2 - TorchicPokedexEntry.page1 > 0 && TorchicPokedexEntry.page2 - TorchicPokedexEntry.page1 <= 255
ASSERT TorchicPokedexEntry.page3 - TorchicPokedexEntry.page1 > 0 && TorchicPokedexEntry.page3 - TorchicPokedexEntry.page1 <= 255
	db TorchicPokedexEntry.page2 - TorchicPokedexEntry.page1, TorchicPokedexEntry.page3 - TorchicPokedexEntry.page1, 0
ASSERT CombuskenPokedexEntry.page2 - CombuskenPokedexEntry.page1 > 0 && CombuskenPokedexEntry.page2 - CombuskenPokedexEntry.page1 <= 255
ASSERT CombuskenPokedexEntry.page3 - CombuskenPokedexEntry.page1 > 0 && CombuskenPokedexEntry.page3 - CombuskenPokedexEntry.page1 <= 255
	db CombuskenPokedexEntry.page2 - CombuskenPokedexEntry.page1, CombuskenPokedexEntry.page3 - CombuskenPokedexEntry.page1, 0
ASSERT BlazikenPokedexEntry.page2 - BlazikenPokedexEntry.page1 > 0 && BlazikenPokedexEntry.page2 - BlazikenPokedexEntry.page1 <= 255
ASSERT BlazikenPokedexEntry.page3 - BlazikenPokedexEntry.page1 > 0 && BlazikenPokedexEntry.page3 - BlazikenPokedexEntry.page1 <= 255
	db BlazikenPokedexEntry.page2 - BlazikenPokedexEntry.page1, BlazikenPokedexEntry.page3 - BlazikenPokedexEntry.page1, 0
ASSERT MudkipPokedexEntry.page2 - MudkipPokedexEntry.page1 > 0 && MudkipPokedexEntry.page2 - MudkipPokedexEntry.page1 <= 255
ASSERT MudkipPokedexEntry.page3 - MudkipPokedexEntry.page1 > 0 && MudkipPokedexEntry.page3 - MudkipPokedexEntry.page1 <= 255
	db MudkipPokedexEntry.page2 - MudkipPokedexEntry.page1, MudkipPokedexEntry.page3 - MudkipPokedexEntry.page1, 0
ASSERT MarshtompPokedexEntry.page2 - MarshtompPokedexEntry.page1 > 0 && MarshtompPokedexEntry.page2 - MarshtompPokedexEntry.page1 <= 255
ASSERT MarshtompPokedexEntry.page3 - MarshtompPokedexEntry.page1 > 0 && MarshtompPokedexEntry.page3 - MarshtompPokedexEntry.page1 <= 255
	db MarshtompPokedexEntry.page2 - MarshtompPokedexEntry.page1, MarshtompPokedexEntry.page3 - MarshtompPokedexEntry.page1, 0
ASSERT SwampertPokedexEntry.page2 - SwampertPokedexEntry.page1 > 0 && SwampertPokedexEntry.page2 - SwampertPokedexEntry.page1 <= 255
ASSERT SwampertPokedexEntry.page3 - SwampertPokedexEntry.page1 > 0 && SwampertPokedexEntry.page3 - SwampertPokedexEntry.page1 <= 255
	db SwampertPokedexEntry.page2 - SwampertPokedexEntry.page1, SwampertPokedexEntry.page3 - SwampertPokedexEntry.page1, 0
ASSERT PoochyenaPokedexEntry.page2 - PoochyenaPokedexEntry.page1 > 0 && PoochyenaPokedexEntry.page2 - PoochyenaPokedexEntry.page1 <= 255
ASSERT PoochyenaPokedexEntry.page3 - PoochyenaPokedexEntry.page1 > 0 && PoochyenaPokedexEntry.page3 - PoochyenaPokedexEntry.page1 <= 255
ASSERT PoochyenaPokedexEntry.page4 - PoochyenaPokedexEntry.page1 > 0 && PoochyenaPokedexEntry.page4 - PoochyenaPokedexEntry.page1 <= 255
	db PoochyenaPokedexEntry.page2 - PoochyenaPokedexEntry.page1, PoochyenaPokedexEntry.page3 - PoochyenaPokedexEntry.page1, PoochyenaPokedexEntry.page4 - PoochyenaPokedexEntry.page1
ASSERT MightyenaPokedexEntry.page2 - MightyenaPokedexEntry.page1 > 0 && MightyenaPokedexEntry.page2 - MightyenaPokedexEntry.page1 <= 255
ASSERT MightyenaPokedexEntry.page3 - MightyenaPokedexEntry.page1 > 0 && MightyenaPokedexEntry.page3 - MightyenaPokedexEntry.page1 <= 255
	db MightyenaPokedexEntry.page2 - MightyenaPokedexEntry.page1, MightyenaPokedexEntry.page3 - MightyenaPokedexEntry.page1, 0
ASSERT WingullPokedexEntry.page2 - WingullPokedexEntry.page1 > 0 && WingullPokedexEntry.page2 - WingullPokedexEntry.page1 <= 255
ASSERT WingullPokedexEntry.page3 - WingullPokedexEntry.page1 > 0 && WingullPokedexEntry.page3 - WingullPokedexEntry.page1 <= 255
	db WingullPokedexEntry.page2 - WingullPokedexEntry.page1, WingullPokedexEntry.page3 - WingullPokedexEntry.page1, 0
ASSERT PelipperPokedexEntry.page2 - PelipperPokedexEntry.page1 > 0 && PelipperPokedexEntry.page2 - PelipperPokedexEntry.page1 <= 255
ASSERT PelipperPokedexEntry.page3 - PelipperPokedexEntry.page1 > 0 && PelipperPokedexEntry.page3 - PelipperPokedexEntry.page1 <= 255
ASSERT PelipperPokedexEntry.page4 - PelipperPokedexEntry.page1 > 0 && PelipperPokedexEntry.page4 - PelipperPokedexEntry.page1 <= 255
	db PelipperPokedexEntry.page2 - PelipperPokedexEntry.page1, PelipperPokedexEntry.page3 - PelipperPokedexEntry.page1, PelipperPokedexEntry.page4 - PelipperPokedexEntry.page1
ASSERT RaltsPokedexEntry.page2 - RaltsPokedexEntry.page1 > 0 && RaltsPokedexEntry.page2 - RaltsPokedexEntry.page1 <= 255
ASSERT RaltsPokedexEntry.page3 - RaltsPokedexEntry.page1 > 0 && RaltsPokedexEntry.page3 - RaltsPokedexEntry.page1 <= 255
	db RaltsPokedexEntry.page2 - RaltsPokedexEntry.page1, RaltsPokedexEntry.page3 - RaltsPokedexEntry.page1, 0
ASSERT KirliaPokedexEntry.page2 - KirliaPokedexEntry.page1 > 0 && KirliaPokedexEntry.page2 - KirliaPokedexEntry.page1 <= 255
ASSERT KirliaPokedexEntry.page3 - KirliaPokedexEntry.page1 > 0 && KirliaPokedexEntry.page3 - KirliaPokedexEntry.page1 <= 255
	db KirliaPokedexEntry.page2 - KirliaPokedexEntry.page1, KirliaPokedexEntry.page3 - KirliaPokedexEntry.page1, 0
ASSERT GardevoirPokedexEntry.page2 - GardevoirPokedexEntry.page1 > 0 && GardevoirPokedexEntry.page2 - GardevoirPokedexEntry.page1 <= 255
ASSERT GardevoirPokedexEntry.page3 - GardevoirPokedexEntry.page1 > 0 && GardevoirPokedexEntry.page3 - GardevoirPokedexEntry.page1 <= 255
	db GardevoirPokedexEntry.page2 - GardevoirPokedexEntry.page1, GardevoirPokedexEntry.page3 - GardevoirPokedexEntry.page1, 0
ASSERT GalladePokedexEntry.page2 - GalladePokedexEntry.page1 > 0 && GalladePokedexEntry.page2 - GalladePokedexEntry.page1 <= 255
	db GalladePokedexEntry.page2 - GalladePokedexEntry.page1, 0, 0
ASSERT ShroomishPokedexEntry.page2 - ShroomishPokedexEntry.page1 > 0 && ShroomishPokedexEntry.page2 - ShroomishPokedexEntry.page1 <= 255
ASSERT ShroomishPokedexEntry.page3 - ShroomishPokedexEntry.page1 > 0 && ShroomishPokedexEntry.page3 - ShroomishPokedexEntry.page1 <= 255
	db ShroomishPokedexEntry.page2 - ShroomishPokedexEntry.page1, ShroomishPokedexEntry.page3 - ShroomishPokedexEntry.page1, 0
ASSERT BreloomPokedexEntry.page2 - BreloomPokedexEntry.page1 > 0 && BreloomPokedexEntry.page2 - BreloomPokedexEntry.page1 <= 255
ASSERT BreloomPokedexEntry.page3 - BreloomPokedexEntry.page1 > 0 && BreloomPokedexEntry.page3 - BreloomPokedexEntry.page1 <= 255
	db BreloomPokedexEntry.page2 - BreloomPokedexEntry.page1, BreloomPokedexEntry.page3 - BreloomPokedexEntry.page1, 0
ASSERT MakuhitaPokedexEntry.page2 - MakuhitaPokedexEntry.page1 > 0 && MakuhitaPokedexEntry.page2 - MakuhitaPokedexEntry.page1 <= 255
ASSERT MakuhitaPokedexEntry.page3 - MakuhitaPokedexEntry.page1 > 0 && MakuhitaPokedexEntry.page3 - MakuhitaPokedexEntry.page1 <= 255
ASSERT MakuhitaPokedexEntry.page4 - MakuhitaPokedexEntry.page1 > 0 && MakuhitaPokedexEntry.page4 - MakuhitaPokedexEntry.page1 <= 255
	db MakuhitaPokedexEntry.page2 - MakuhitaPokedexEntry.page1, MakuhitaPokedexEntry.page3 - MakuhitaPokedexEntry.page1, MakuhitaPokedexEntry.page4 - MakuhitaPokedexEntry.page1
ASSERT HariyamaPokedexEntry.page2 - HariyamaPokedexEntry.page1 > 0 && HariyamaPokedexEntry.page2 - HariyamaPokedexEntry.page1 <= 255
ASSERT HariyamaPokedexEntry.page3 - HariyamaPokedexEntry.page1 > 0 && HariyamaPokedexEntry.page3 - HariyamaPokedexEntry.page1 <= 255
ASSERT HariyamaPokedexEntry.page4 - HariyamaPokedexEntry.page1 > 0 && HariyamaPokedexEntry.page4 - HariyamaPokedexEntry.page1 <= 255
	db HariyamaPokedexEntry.page2 - HariyamaPokedexEntry.page1, HariyamaPokedexEntry.page3 - HariyamaPokedexEntry.page1, HariyamaPokedexEntry.page4 - HariyamaPokedexEntry.page1
ASSERT SkittyPokedexEntry.page2 - SkittyPokedexEntry.page1 > 0 && SkittyPokedexEntry.page2 - SkittyPokedexEntry.page1 <= 255
ASSERT SkittyPokedexEntry.page3 - SkittyPokedexEntry.page1 > 0 && SkittyPokedexEntry.page3 - SkittyPokedexEntry.page1 <= 255
	db SkittyPokedexEntry.page2 - SkittyPokedexEntry.page1, SkittyPokedexEntry.page3 - SkittyPokedexEntry.page1, 0
ASSERT DelcattyPokedexEntry.page2 - DelcattyPokedexEntry.page1 > 0 && DelcattyPokedexEntry.page2 - DelcattyPokedexEntry.page1 <= 255
ASSERT DelcattyPokedexEntry.page3 - DelcattyPokedexEntry.page1 > 0 && DelcattyPokedexEntry.page3 - DelcattyPokedexEntry.page1 <= 255
	db DelcattyPokedexEntry.page2 - DelcattyPokedexEntry.page1, DelcattyPokedexEntry.page3 - DelcattyPokedexEntry.page1, 0
ASSERT SableyePokedexEntry.page2 - SableyePokedexEntry.page1 > 0 && SableyePokedexEntry.page2 - SableyePokedexEntry.page1 <= 255
ASSERT SableyePokedexEntry.page3 - SableyePokedexEntry.page1 > 0 && SableyePokedexEntry.page3 - SableyePokedexEntry.page1 <= 255
	db SableyePokedexEntry.page2 - SableyePokedexEntry.page1, SableyePokedexEntry.page3 - SableyePokedexEntry.page1, 0
ASSERT MawilePokedexEntry.page2 - MawilePokedexEntry.page1 > 0 && MawilePokedexEntry.page2 - MawilePokedexEntry.page1 <= 255
ASSERT MawilePokedexEntry.page3 - MawilePokedexEntry.page1 > 0 && MawilePokedexEntry.page3 - MawilePokedexEntry.page1 <= 255
ASSERT MawilePokedexEntry.page4 - MawilePokedexEntry.page1 > 0 && MawilePokedexEntry.page4 - MawilePokedexEntry.page1 <= 255
	db MawilePokedexEntry.page2 - MawilePokedexEntry.page1, MawilePokedexEntry.page3 - MawilePokedexEntry.page1, MawilePokedexEntry.page4 - MawilePokedexEntry.page1
ASSERT AronPokedexEntry.page2 - AronPokedexEntry.page1 > 0 && AronPokedexEntry.page2 - AronPokedexEntry.page1 <= 255
ASSERT AronPokedexEntry.page3 - AronPokedexEntry.page1 > 0 && AronPokedexEntry.page3 - AronPokedexEntry.page1 <= 255
ASSERT AronPokedexEntry.page4 - AronPokedexEntry.page1 > 0 && AronPokedexEntry.page4 - AronPokedexEntry.page1 <= 255
	db AronPokedexEntry.page2 - AronPokedexEntry.page1, AronPokedexEntry.page3 - AronPokedexEntry.page1, AronPokedexEntry.page4 - AronPokedexEntry.page1
ASSERT LaironPokedexEntry.page2 - LaironPokedexEntry.page1 > 0 && LaironPokedexEntry.page2 - LaironPokedexEntry.page1 <= 255
ASSERT LaironPokedexEntry.page3 - LaironPokedexEntry.page1 > 0 && LaironPokedexEntry.page3 - LaironPokedexEntry.page1 <= 255
ASSERT LaironPokedexEntry.page4 - LaironPokedexEntry.page1 > 0 && LaironPokedexEntry.page4 - LaironPokedexEntry.page1 <= 255
	db LaironPokedexEntry.page2 - LaironPokedexEntry.page1, LaironPokedexEntry.page3 - LaironPokedexEntry.page1, LaironPokedexEntry.page4 - LaironPokedexEntry.page1
ASSERT AggronPokedexEntry.page2 - AggronPokedexEntry.page1 > 0 && AggronPokedexEntry.page2 - AggronPokedexEntry.page1 <= 255
ASSERT AggronPokedexEntry.page3 - AggronPokedexEntry.page1 > 0 && AggronPokedexEntry.page3 - AggronPokedexEntry.page1 <= 255
ASSERT AggronPokedexEntry.page4 - AggronPokedexEntry.page1 > 0 && AggronPokedexEntry.page4 - AggronPokedexEntry.page1 <= 255
	db AggronPokedexEntry.page2 - AggronPokedexEntry.page1, AggronPokedexEntry.page3 - AggronPokedexEntry.page1, AggronPokedexEntry.page4 - AggronPokedexEntry.page1
ASSERT MedititePokedexEntry.page2 - MedititePokedexEntry.page1 > 0 && MedititePokedexEntry.page2 - MedititePokedexEntry.page1 <= 255
ASSERT MedititePokedexEntry.page3 - MedititePokedexEntry.page1 > 0 && MedititePokedexEntry.page3 - MedititePokedexEntry.page1 <= 255
ASSERT MedititePokedexEntry.page4 - MedititePokedexEntry.page1 > 0 && MedititePokedexEntry.page4 - MedititePokedexEntry.page1 <= 255
	db MedititePokedexEntry.page2 - MedititePokedexEntry.page1, MedititePokedexEntry.page3 - MedititePokedexEntry.page1, MedititePokedexEntry.page4 - MedititePokedexEntry.page1
ASSERT MedichamPokedexEntry.page2 - MedichamPokedexEntry.page1 > 0 && MedichamPokedexEntry.page2 - MedichamPokedexEntry.page1 <= 255
ASSERT MedichamPokedexEntry.page3 - MedichamPokedexEntry.page1 > 0 && MedichamPokedexEntry.page3 - MedichamPokedexEntry.page1 <= 255
	db MedichamPokedexEntry.page2 - MedichamPokedexEntry.page1, MedichamPokedexEntry.page3 - MedichamPokedexEntry.page1, 0
ASSERT ElectrikePokedexEntry.page2 - ElectrikePokedexEntry.page1 > 0 && ElectrikePokedexEntry.page2 - ElectrikePokedexEntry.page1 <= 255
ASSERT ElectrikePokedexEntry.page3 - ElectrikePokedexEntry.page1 > 0 && ElectrikePokedexEntry.page3 - ElectrikePokedexEntry.page1 <= 255
ASSERT ElectrikePokedexEntry.page4 - ElectrikePokedexEntry.page1 > 0 && ElectrikePokedexEntry.page4 - ElectrikePokedexEntry.page1 <= 255
	db ElectrikePokedexEntry.page2 - ElectrikePokedexEntry.page1, ElectrikePokedexEntry.page3 - ElectrikePokedexEntry.page1, ElectrikePokedexEntry.page4 - ElectrikePokedexEntry.page1
ASSERT ManectricPokedexEntry.page2 - ManectricPokedexEntry.page1 > 0 && ManectricPokedexEntry.page2 - ManectricPokedexEntry.page1 <= 255
ASSERT ManectricPokedexEntry.page3 - ManectricPokedexEntry.page1 > 0 && ManectricPokedexEntry.page3 - ManectricPokedexEntry.page1 <= 255
ASSERT ManectricPokedexEntry.page4 - ManectricPokedexEntry.page1 > 0 && ManectricPokedexEntry.page4 - ManectricPokedexEntry.page1 <= 255
	db ManectricPokedexEntry.page2 - ManectricPokedexEntry.page1, ManectricPokedexEntry.page3 - ManectricPokedexEntry.page1, ManectricPokedexEntry.page4 - ManectricPokedexEntry.page1
ASSERT RoseliaPokedexEntry.page2 - RoseliaPokedexEntry.page1 > 0 && RoseliaPokedexEntry.page2 - RoseliaPokedexEntry.page1 <= 255
ASSERT RoseliaPokedexEntry.page3 - RoseliaPokedexEntry.page1 > 0 && RoseliaPokedexEntry.page3 - RoseliaPokedexEntry.page1 <= 255
ASSERT RoseliaPokedexEntry.page4 - RoseliaPokedexEntry.page1 > 0 && RoseliaPokedexEntry.page4 - RoseliaPokedexEntry.page1 <= 255
	db RoseliaPokedexEntry.page2 - RoseliaPokedexEntry.page1, RoseliaPokedexEntry.page3 - RoseliaPokedexEntry.page1, RoseliaPokedexEntry.page4 - RoseliaPokedexEntry.page1
ASSERT RoseradePokedexEntry.page2 - RoseradePokedexEntry.page1 > 0 && RoseradePokedexEntry.page2 - RoseradePokedexEntry.page1 <= 255
	db RoseradePokedexEntry.page2 - RoseradePokedexEntry.page1, 0, 0
ASSERT CarvanhaPokedexEntry.page2 - CarvanhaPokedexEntry.page1 > 0 && CarvanhaPokedexEntry.page2 - CarvanhaPokedexEntry.page1 <= 255
ASSERT CarvanhaPokedexEntry.page3 - CarvanhaPokedexEntry.page1 > 0 && CarvanhaPokedexEntry.page3 - CarvanhaPokedexEntry.page1 <= 255
ASSERT CarvanhaPokedexEntry.page4 - CarvanhaPokedexEntry.page1 > 0 && CarvanhaPokedexEntry.page4 - CarvanhaPokedexEntry.page1 <= 255
	db CarvanhaPokedexEntry.page2 - CarvanhaPokedexEntry.page1, CarvanhaPokedexEntry.page3 - CarvanhaPokedexEntry.page1, CarvanhaPokedexEntry.page4 - CarvanhaPokedexEntry.page1
ASSERT SharpedoPokedexEntry.page2 - SharpedoPokedexEntry.page1 > 0 && SharpedoPokedexEntry.page2 - SharpedoPokedexEntry.page1 <= 255
ASSERT SharpedoPokedexEntry.page3 - SharpedoPokedexEntry.page1 > 0 && SharpedoPokedexEntry.page3 - SharpedoPokedexEntry.page1 <= 255
	db SharpedoPokedexEntry.page2 - SharpedoPokedexEntry.page1, SharpedoPokedexEntry.page3 - SharpedoPokedexEntry.page1, 0
ASSERT NumelPokedexEntry.page2 - NumelPokedexEntry.page1 > 0 && NumelPokedexEntry.page2 - NumelPokedexEntry.page1 <= 255
ASSERT NumelPokedexEntry.page3 - NumelPokedexEntry.page1 > 0 && NumelPokedexEntry.page3 - NumelPokedexEntry.page1 <= 255
ASSERT NumelPokedexEntry.page4 - NumelPokedexEntry.page1 > 0 && NumelPokedexEntry.page4 - NumelPokedexEntry.page1 <= 255
	db NumelPokedexEntry.page2 - NumelPokedexEntry.page1, NumelPokedexEntry.page3 - NumelPokedexEntry.page1, NumelPokedexEntry.page4 - NumelPokedexEntry.page1
ASSERT CameruptPokedexEntry.page2 - CameruptPokedexEntry.page1 > 0 && CameruptPokedexEntry.page2 - CameruptPokedexEntry.page1 <= 255
ASSERT CameruptPokedexEntry.page3 - CameruptPokedexEntry.page1 > 0 && CameruptPokedexEntry.page3 - CameruptPokedexEntry.page1 <= 255
ASSERT CameruptPokedexEntry.page4 - CameruptPokedexEntry.page1 > 0 && CameruptPokedexEntry.page4 - CameruptPokedexEntry.page1 <= 255
	db CameruptPokedexEntry.page2 - CameruptPokedexEntry.page1, CameruptPokedexEntry.page3 - CameruptPokedexEntry.page1, CameruptPokedexEntry.page4 - CameruptPokedexEntry.page1
ASSERT TorkoalPokedexEntry.page2 - TorkoalPokedexEntry.page1 > 0 && TorkoalPokedexEntry.page2 - TorkoalPokedexEntry.page1 <= 255
ASSERT TorkoalPokedexEntry.page3 - TorkoalPokedexEntry.page1 > 0 && TorkoalPokedexEntry.page3 - TorkoalPokedexEntry.page1 <= 255
	db TorkoalPokedexEntry.page2 - TorkoalPokedexEntry.page1, TorkoalPokedexEntry.page3 - TorkoalPokedexEntry.page1, 0
ASSERT TrapinchPokedexEntry.page2 - TrapinchPokedexEntry.page1 > 0 && TrapinchPokedexEntry.page2 - TrapinchPokedexEntry.page1 <= 255
ASSERT TrapinchPokedexEntry.page3 - TrapinchPokedexEntry.page1 > 0 && TrapinchPokedexEntry.page3 - TrapinchPokedexEntry.page1 <= 255
	db TrapinchPokedexEntry.page2 - TrapinchPokedexEntry.page1, TrapinchPokedexEntry.page3 - TrapinchPokedexEntry.page1, 0
ASSERT VibravaPokedexEntry.page2 - VibravaPokedexEntry.page1 > 0 && VibravaPokedexEntry.page2 - VibravaPokedexEntry.page1 <= 255
ASSERT VibravaPokedexEntry.page3 - VibravaPokedexEntry.page1 > 0 && VibravaPokedexEntry.page3 - VibravaPokedexEntry.page1 <= 255
ASSERT VibravaPokedexEntry.page4 - VibravaPokedexEntry.page1 > 0 && VibravaPokedexEntry.page4 - VibravaPokedexEntry.page1 <= 255
	db VibravaPokedexEntry.page2 - VibravaPokedexEntry.page1, VibravaPokedexEntry.page3 - VibravaPokedexEntry.page1, VibravaPokedexEntry.page4 - VibravaPokedexEntry.page1
ASSERT FlygonPokedexEntry.page2 - FlygonPokedexEntry.page1 > 0 && FlygonPokedexEntry.page2 - FlygonPokedexEntry.page1 <= 255
ASSERT FlygonPokedexEntry.page3 - FlygonPokedexEntry.page1 > 0 && FlygonPokedexEntry.page3 - FlygonPokedexEntry.page1 <= 255
	db FlygonPokedexEntry.page2 - FlygonPokedexEntry.page1, FlygonPokedexEntry.page3 - FlygonPokedexEntry.page1, 0
ASSERT SwabluPokedexEntry.page2 - SwabluPokedexEntry.page1 > 0 && SwabluPokedexEntry.page2 - SwabluPokedexEntry.page1 <= 255
ASSERT SwabluPokedexEntry.page3 - SwabluPokedexEntry.page1 > 0 && SwabluPokedexEntry.page3 - SwabluPokedexEntry.page1 <= 255
	db SwabluPokedexEntry.page2 - SwabluPokedexEntry.page1, SwabluPokedexEntry.page3 - SwabluPokedexEntry.page1, 0
ASSERT AltariaPokedexEntry.page2 - AltariaPokedexEntry.page1 > 0 && AltariaPokedexEntry.page2 - AltariaPokedexEntry.page1 <= 255
ASSERT AltariaPokedexEntry.page3 - AltariaPokedexEntry.page1 > 0 && AltariaPokedexEntry.page3 - AltariaPokedexEntry.page1 <= 255
	db AltariaPokedexEntry.page2 - AltariaPokedexEntry.page1, AltariaPokedexEntry.page3 - AltariaPokedexEntry.page1, 0
ASSERT ZangoosePokedexEntry.page2 - ZangoosePokedexEntry.page1 > 0 && ZangoosePokedexEntry.page2 - ZangoosePokedexEntry.page1 <= 255
ASSERT ZangoosePokedexEntry.page3 - ZangoosePokedexEntry.page1 > 0 && ZangoosePokedexEntry.page3 - ZangoosePokedexEntry.page1 <= 255
	db ZangoosePokedexEntry.page2 - ZangoosePokedexEntry.page1, ZangoosePokedexEntry.page3 - ZangoosePokedexEntry.page1, 0
ASSERT SeviperPokedexEntry.page2 - SeviperPokedexEntry.page1 > 0 && SeviperPokedexEntry.page2 - SeviperPokedexEntry.page1 <= 255
ASSERT SeviperPokedexEntry.page3 - SeviperPokedexEntry.page1 > 0 && SeviperPokedexEntry.page3 - SeviperPokedexEntry.page1 <= 255
	db SeviperPokedexEntry.page2 - SeviperPokedexEntry.page1, SeviperPokedexEntry.page3 - SeviperPokedexEntry.page1, 0
ASSERT LunatonePokedexEntry.page2 - LunatonePokedexEntry.page1 > 0 && LunatonePokedexEntry.page2 - LunatonePokedexEntry.page1 <= 255
ASSERT LunatonePokedexEntry.page3 - LunatonePokedexEntry.page1 > 0 && LunatonePokedexEntry.page3 - LunatonePokedexEntry.page1 <= 255
	db LunatonePokedexEntry.page2 - LunatonePokedexEntry.page1, LunatonePokedexEntry.page3 - LunatonePokedexEntry.page1, 0
ASSERT SolrockPokedexEntry.page2 - SolrockPokedexEntry.page1 > 0 && SolrockPokedexEntry.page2 - SolrockPokedexEntry.page1 <= 255
ASSERT SolrockPokedexEntry.page3 - SolrockPokedexEntry.page1 > 0 && SolrockPokedexEntry.page3 - SolrockPokedexEntry.page1 <= 255
	db SolrockPokedexEntry.page2 - SolrockPokedexEntry.page1, SolrockPokedexEntry.page3 - SolrockPokedexEntry.page1, 0
ASSERT BarboachPokedexEntry.page2 - BarboachPokedexEntry.page1 > 0 && BarboachPokedexEntry.page2 - BarboachPokedexEntry.page1 <= 255
ASSERT BarboachPokedexEntry.page3 - BarboachPokedexEntry.page1 > 0 && BarboachPokedexEntry.page3 - BarboachPokedexEntry.page1 <= 255
	db BarboachPokedexEntry.page2 - BarboachPokedexEntry.page1, BarboachPokedexEntry.page3 - BarboachPokedexEntry.page1, 0
ASSERT WhiscashPokedexEntry.page2 - WhiscashPokedexEntry.page1 > 0 && WhiscashPokedexEntry.page2 - WhiscashPokedexEntry.page1 <= 255
ASSERT WhiscashPokedexEntry.page3 - WhiscashPokedexEntry.page1 > 0 && WhiscashPokedexEntry.page3 - WhiscashPokedexEntry.page1 <= 255
ASSERT WhiscashPokedexEntry.page4 - WhiscashPokedexEntry.page1 > 0 && WhiscashPokedexEntry.page4 - WhiscashPokedexEntry.page1 <= 255
	db WhiscashPokedexEntry.page2 - WhiscashPokedexEntry.page1, WhiscashPokedexEntry.page3 - WhiscashPokedexEntry.page1, WhiscashPokedexEntry.page4 - WhiscashPokedexEntry.page1
ASSERT CorphishPokedexEntry.page2 - CorphishPokedexEntry.page1 > 0 && CorphishPokedexEntry.page2 - CorphishPokedexEntry.page1 <= 255
ASSERT CorphishPokedexEntry.page3 - CorphishPokedexEntry.page1 > 0 && CorphishPokedexEntry.page3 - CorphishPokedexEntry.page1 <= 255
	db CorphishPokedexEntry.page2 - CorphishPokedexEntry.page1, CorphishPokedexEntry.page3 - CorphishPokedexEntry.page1, 0
ASSERT CrawdauntPokedexEntry.page2 - CrawdauntPokedexEntry.page1 > 0 && CrawdauntPokedexEntry.page2 - CrawdauntPokedexEntry.page1 <= 255
ASSERT CrawdauntPokedexEntry.page3 - CrawdauntPokedexEntry.page1 > 0 && CrawdauntPokedexEntry.page3 - CrawdauntPokedexEntry.page1 <= 255
ASSERT CrawdauntPokedexEntry.page4 - CrawdauntPokedexEntry.page1 > 0 && CrawdauntPokedexEntry.page4 - CrawdauntPokedexEntry.page1 <= 255
	db CrawdauntPokedexEntry.page2 - CrawdauntPokedexEntry.page1, CrawdauntPokedexEntry.page3 - CrawdauntPokedexEntry.page1, CrawdauntPokedexEntry.page4 - CrawdauntPokedexEntry.page1
ASSERT BaltoyPokedexEntry.page2 - BaltoyPokedexEntry.page1 > 0 && BaltoyPokedexEntry.page2 - BaltoyPokedexEntry.page1 <= 255
ASSERT BaltoyPokedexEntry.page3 - BaltoyPokedexEntry.page1 > 0 && BaltoyPokedexEntry.page3 - BaltoyPokedexEntry.page1 <= 255
	db BaltoyPokedexEntry.page2 - BaltoyPokedexEntry.page1, BaltoyPokedexEntry.page3 - BaltoyPokedexEntry.page1, 0
ASSERT ClaydolPokedexEntry.page2 - ClaydolPokedexEntry.page1 > 0 && ClaydolPokedexEntry.page2 - ClaydolPokedexEntry.page1 <= 255
ASSERT ClaydolPokedexEntry.page3 - ClaydolPokedexEntry.page1 > 0 && ClaydolPokedexEntry.page3 - ClaydolPokedexEntry.page1 <= 255
	db ClaydolPokedexEntry.page2 - ClaydolPokedexEntry.page1, ClaydolPokedexEntry.page3 - ClaydolPokedexEntry.page1, 0
ASSERT LileepPokedexEntry.page2 - LileepPokedexEntry.page1 > 0 && LileepPokedexEntry.page2 - LileepPokedexEntry.page1 <= 255
ASSERT LileepPokedexEntry.page3 - LileepPokedexEntry.page1 > 0 && LileepPokedexEntry.page3 - LileepPokedexEntry.page1 <= 255
ASSERT LileepPokedexEntry.page4 - LileepPokedexEntry.page1 > 0 && LileepPokedexEntry.page4 - LileepPokedexEntry.page1 <= 255
	db LileepPokedexEntry.page2 - LileepPokedexEntry.page1, LileepPokedexEntry.page3 - LileepPokedexEntry.page1, LileepPokedexEntry.page4 - LileepPokedexEntry.page1
ASSERT CradilyPokedexEntry.page2 - CradilyPokedexEntry.page1 > 0 && CradilyPokedexEntry.page2 - CradilyPokedexEntry.page1 <= 255
ASSERT CradilyPokedexEntry.page3 - CradilyPokedexEntry.page1 > 0 && CradilyPokedexEntry.page3 - CradilyPokedexEntry.page1 <= 255
	db CradilyPokedexEntry.page2 - CradilyPokedexEntry.page1, CradilyPokedexEntry.page3 - CradilyPokedexEntry.page1, 0
ASSERT AnorithPokedexEntry.page2 - AnorithPokedexEntry.page1 > 0 && AnorithPokedexEntry.page2 - AnorithPokedexEntry.page1 <= 255
ASSERT AnorithPokedexEntry.page3 - AnorithPokedexEntry.page1 > 0 && AnorithPokedexEntry.page3 - AnorithPokedexEntry.page1 <= 255
ASSERT AnorithPokedexEntry.page4 - AnorithPokedexEntry.page1 > 0 && AnorithPokedexEntry.page4 - AnorithPokedexEntry.page1 <= 255
	db AnorithPokedexEntry.page2 - AnorithPokedexEntry.page1, AnorithPokedexEntry.page3 - AnorithPokedexEntry.page1, AnorithPokedexEntry.page4 - AnorithPokedexEntry.page1
ASSERT ArmaldoPokedexEntry.page2 - ArmaldoPokedexEntry.page1 > 0 && ArmaldoPokedexEntry.page2 - ArmaldoPokedexEntry.page1 <= 255
ASSERT ArmaldoPokedexEntry.page3 - ArmaldoPokedexEntry.page1 > 0 && ArmaldoPokedexEntry.page3 - ArmaldoPokedexEntry.page1 <= 255
	db ArmaldoPokedexEntry.page2 - ArmaldoPokedexEntry.page1, ArmaldoPokedexEntry.page3 - ArmaldoPokedexEntry.page1, 0
ASSERT FeebasPokedexEntry.page2 - FeebasPokedexEntry.page1 > 0 && FeebasPokedexEntry.page2 - FeebasPokedexEntry.page1 <= 255
ASSERT FeebasPokedexEntry.page3 - FeebasPokedexEntry.page1 > 0 && FeebasPokedexEntry.page3 - FeebasPokedexEntry.page1 <= 255
	db FeebasPokedexEntry.page2 - FeebasPokedexEntry.page1, FeebasPokedexEntry.page3 - FeebasPokedexEntry.page1, 0
ASSERT MiloticPokedexEntry.page2 - MiloticPokedexEntry.page1 > 0 && MiloticPokedexEntry.page2 - MiloticPokedexEntry.page1 <= 255
ASSERT MiloticPokedexEntry.page3 - MiloticPokedexEntry.page1 > 0 && MiloticPokedexEntry.page3 - MiloticPokedexEntry.page1 <= 255
	db MiloticPokedexEntry.page2 - MiloticPokedexEntry.page1, MiloticPokedexEntry.page3 - MiloticPokedexEntry.page1, 0
ASSERT ShuppetPokedexEntry.page2 - ShuppetPokedexEntry.page1 > 0 && ShuppetPokedexEntry.page2 - ShuppetPokedexEntry.page1 <= 255
ASSERT ShuppetPokedexEntry.page3 - ShuppetPokedexEntry.page1 > 0 && ShuppetPokedexEntry.page3 - ShuppetPokedexEntry.page1 <= 255
	db ShuppetPokedexEntry.page2 - ShuppetPokedexEntry.page1, ShuppetPokedexEntry.page3 - ShuppetPokedexEntry.page1, 0
ASSERT BanettePokedexEntry.page2 - BanettePokedexEntry.page1 > 0 && BanettePokedexEntry.page2 - BanettePokedexEntry.page1 <= 255
ASSERT BanettePokedexEntry.page3 - BanettePokedexEntry.page1 > 0 && BanettePokedexEntry.page3 - BanettePokedexEntry.page1 <= 255
	db BanettePokedexEntry.page2 - BanettePokedexEntry.page1, BanettePokedexEntry.page3 - BanettePokedexEntry.page1, 0
ASSERT DuskullPokedexEntry.page2 - DuskullPokedexEntry.page1 > 0 && DuskullPokedexEntry.page2 - DuskullPokedexEntry.page1 <= 255
ASSERT DuskullPokedexEntry.page3 - DuskullPokedexEntry.page1 > 0 && DuskullPokedexEntry.page3 - DuskullPokedexEntry.page1 <= 255
	db DuskullPokedexEntry.page2 - DuskullPokedexEntry.page1, DuskullPokedexEntry.page3 - DuskullPokedexEntry.page1, 0
ASSERT DusclopsPokedexEntry.page2 - DusclopsPokedexEntry.page1 > 0 && DusclopsPokedexEntry.page2 - DusclopsPokedexEntry.page1 <= 255
ASSERT DusclopsPokedexEntry.page3 - DusclopsPokedexEntry.page1 > 0 && DusclopsPokedexEntry.page3 - DusclopsPokedexEntry.page1 <= 255
ASSERT DusclopsPokedexEntry.page4 - DusclopsPokedexEntry.page1 > 0 && DusclopsPokedexEntry.page4 - DusclopsPokedexEntry.page1 <= 255
	db DusclopsPokedexEntry.page2 - DusclopsPokedexEntry.page1, DusclopsPokedexEntry.page3 - DusclopsPokedexEntry.page1, DusclopsPokedexEntry.page4 - DusclopsPokedexEntry.page1
ASSERT DusknoirPokedexEntry.page2 - DusknoirPokedexEntry.page1 > 0 && DusknoirPokedexEntry.page2 - DusknoirPokedexEntry.page1 <= 255
	db DusknoirPokedexEntry.page2 - DusknoirPokedexEntry.page1, 0, 0
ASSERT AbsolPokedexEntry.page2 - AbsolPokedexEntry.page1 > 0 && AbsolPokedexEntry.page2 - AbsolPokedexEntry.page1 <= 255
ASSERT AbsolPokedexEntry.page3 - AbsolPokedexEntry.page1 > 0 && AbsolPokedexEntry.page3 - AbsolPokedexEntry.page1 <= 255
ASSERT AbsolPokedexEntry.page4 - AbsolPokedexEntry.page1 > 0 && AbsolPokedexEntry.page4 - AbsolPokedexEntry.page1 <= 255
	db AbsolPokedexEntry.page2 - AbsolPokedexEntry.page1, AbsolPokedexEntry.page3 - AbsolPokedexEntry.page1, AbsolPokedexEntry.page4 - AbsolPokedexEntry.page1
ASSERT SnoruntPokedexEntry.page2 - SnoruntPokedexEntry.page1 > 0 && SnoruntPokedexEntry.page2 - SnoruntPokedexEntry.page1 <= 255
ASSERT SnoruntPokedexEntry.page3 - SnoruntPokedexEntry.page1 > 0 && SnoruntPokedexEntry.page3 - SnoruntPokedexEntry.page1 <= 255
ASSERT SnoruntPokedexEntry.page4 - SnoruntPokedexEntry.page1 > 0 && SnoruntPokedexEntry.page4 - SnoruntPokedexEntry.page1 <= 255
	db SnoruntPokedexEntry.page2 - SnoruntPokedexEntry.page1, SnoruntPokedexEntry.page3 - SnoruntPokedexEntry.page1, SnoruntPokedexEntry.page4 - SnoruntPokedexEntry.page1
ASSERT GlaliePokedexEntry.page2 - GlaliePokedexEntry.page1 > 0 && GlaliePokedexEntry.page2 - GlaliePokedexEntry.page1 <= 255
ASSERT GlaliePokedexEntry.page3 - GlaliePokedexEntry.page1 > 0 && GlaliePokedexEntry.page3 - GlaliePokedexEntry.page1 <= 255
	db GlaliePokedexEntry.page2 - GlaliePokedexEntry.page1, GlaliePokedexEntry.page3 - GlaliePokedexEntry.page1, 0
ASSERT FroslassPokedexEntry.page2 - FroslassPokedexEntry.page1 > 0 && FroslassPokedexEntry.page2 - FroslassPokedexEntry.page1 <= 255
	db FroslassPokedexEntry.page2 - FroslassPokedexEntry.page1, 0, 0
ASSERT SphealPokedexEntry.page2 - SphealPokedexEntry.page1 > 0 && SphealPokedexEntry.page2 - SphealPokedexEntry.page1 <= 255
ASSERT SphealPokedexEntry.page3 - SphealPokedexEntry.page1 > 0 && SphealPokedexEntry.page3 - SphealPokedexEntry.page1 <= 255
	db SphealPokedexEntry.page2 - SphealPokedexEntry.page1, SphealPokedexEntry.page3 - SphealPokedexEntry.page1, 0
ASSERT SealeoPokedexEntry.page2 - SealeoPokedexEntry.page1 > 0 && SealeoPokedexEntry.page2 - SealeoPokedexEntry.page1 <= 255
ASSERT SealeoPokedexEntry.page3 - SealeoPokedexEntry.page1 > 0 && SealeoPokedexEntry.page3 - SealeoPokedexEntry.page1 <= 255
	db SealeoPokedexEntry.page2 - SealeoPokedexEntry.page1, SealeoPokedexEntry.page3 - SealeoPokedexEntry.page1, 0
ASSERT WalreinPokedexEntry.page2 - WalreinPokedexEntry.page1 > 0 && WalreinPokedexEntry.page2 - WalreinPokedexEntry.page1 <= 255
ASSERT WalreinPokedexEntry.page3 - WalreinPokedexEntry.page1 > 0 && WalreinPokedexEntry.page3 - WalreinPokedexEntry.page1 <= 255
	db WalreinPokedexEntry.page2 - WalreinPokedexEntry.page1, WalreinPokedexEntry.page3 - WalreinPokedexEntry.page1, 0
ASSERT BagonPokedexEntry.page2 - BagonPokedexEntry.page1 > 0 && BagonPokedexEntry.page2 - BagonPokedexEntry.page1 <= 255
ASSERT BagonPokedexEntry.page3 - BagonPokedexEntry.page1 > 0 && BagonPokedexEntry.page3 - BagonPokedexEntry.page1 <= 255
ASSERT BagonPokedexEntry.page4 - BagonPokedexEntry.page1 > 0 && BagonPokedexEntry.page4 - BagonPokedexEntry.page1 <= 255
	db BagonPokedexEntry.page2 - BagonPokedexEntry.page1, BagonPokedexEntry.page3 - BagonPokedexEntry.page1, BagonPokedexEntry.page4 - BagonPokedexEntry.page1
ASSERT ShelgonPokedexEntry.page2 - ShelgonPokedexEntry.page1 > 0 && ShelgonPokedexEntry.page2 - ShelgonPokedexEntry.page1 <= 255
ASSERT ShelgonPokedexEntry.page3 - ShelgonPokedexEntry.page1 > 0 && ShelgonPokedexEntry.page3 - ShelgonPokedexEntry.page1 <= 255
	db ShelgonPokedexEntry.page2 - ShelgonPokedexEntry.page1, ShelgonPokedexEntry.page3 - ShelgonPokedexEntry.page1, 0
ASSERT SalamencePokedexEntry.page2 - SalamencePokedexEntry.page1 > 0 && SalamencePokedexEntry.page2 - SalamencePokedexEntry.page1 <= 255
ASSERT SalamencePokedexEntry.page3 - SalamencePokedexEntry.page1 > 0 && SalamencePokedexEntry.page3 - SalamencePokedexEntry.page1 <= 255
ASSERT SalamencePokedexEntry.page4 - SalamencePokedexEntry.page1 > 0 && SalamencePokedexEntry.page4 - SalamencePokedexEntry.page1 <= 255
	db SalamencePokedexEntry.page2 - SalamencePokedexEntry.page1, SalamencePokedexEntry.page3 - SalamencePokedexEntry.page1, SalamencePokedexEntry.page4 - SalamencePokedexEntry.page1
ASSERT BeldumPokedexEntry.page2 - BeldumPokedexEntry.page1 > 0 && BeldumPokedexEntry.page2 - BeldumPokedexEntry.page1 <= 255
ASSERT BeldumPokedexEntry.page3 - BeldumPokedexEntry.page1 > 0 && BeldumPokedexEntry.page3 - BeldumPokedexEntry.page1 <= 255
	db BeldumPokedexEntry.page2 - BeldumPokedexEntry.page1, BeldumPokedexEntry.page3 - BeldumPokedexEntry.page1, 0
ASSERT MetangPokedexEntry.page2 - MetangPokedexEntry.page1 > 0 && MetangPokedexEntry.page2 - MetangPokedexEntry.page1 <= 255
ASSERT MetangPokedexEntry.page3 - MetangPokedexEntry.page1 > 0 && MetangPokedexEntry.page3 - MetangPokedexEntry.page1 <= 255
	db MetangPokedexEntry.page2 - MetangPokedexEntry.page1, MetangPokedexEntry.page3 - MetangPokedexEntry.page1, 0
ASSERT MetagrossPokedexEntry.page2 - MetagrossPokedexEntry.page1 > 0 && MetagrossPokedexEntry.page2 - MetagrossPokedexEntry.page1 <= 255
ASSERT MetagrossPokedexEntry.page3 - MetagrossPokedexEntry.page1 > 0 && MetagrossPokedexEntry.page3 - MetagrossPokedexEntry.page1 <= 255
ASSERT MetagrossPokedexEntry.page4 - MetagrossPokedexEntry.page1 > 0 && MetagrossPokedexEntry.page4 - MetagrossPokedexEntry.page1 <= 255
	db MetagrossPokedexEntry.page2 - MetagrossPokedexEntry.page1, MetagrossPokedexEntry.page3 - MetagrossPokedexEntry.page1, MetagrossPokedexEntry.page4 - MetagrossPokedexEntry.page1
ASSERT RegirockPokedexEntry.page2 - RegirockPokedexEntry.page1 > 0 && RegirockPokedexEntry.page2 - RegirockPokedexEntry.page1 <= 255
ASSERT RegirockPokedexEntry.page3 - RegirockPokedexEntry.page1 > 0 && RegirockPokedexEntry.page3 - RegirockPokedexEntry.page1 <= 255
	db RegirockPokedexEntry.page2 - RegirockPokedexEntry.page1, RegirockPokedexEntry.page3 - RegirockPokedexEntry.page1, 0
ASSERT RegicePokedexEntry.page2 - RegicePokedexEntry.page1 > 0 && RegicePokedexEntry.page2 - RegicePokedexEntry.page1 <= 255
ASSERT RegicePokedexEntry.page3 - RegicePokedexEntry.page1 > 0 && RegicePokedexEntry.page3 - RegicePokedexEntry.page1 <= 255
	db RegicePokedexEntry.page2 - RegicePokedexEntry.page1, RegicePokedexEntry.page3 - RegicePokedexEntry.page1, 0
ASSERT RegisteelPokedexEntry.page2 - RegisteelPokedexEntry.page1 > 0 && RegisteelPokedexEntry.page2 - RegisteelPokedexEntry.page1 <= 255
ASSERT RegisteelPokedexEntry.page3 - RegisteelPokedexEntry.page1 > 0 && RegisteelPokedexEntry.page3 - RegisteelPokedexEntry.page1 <= 255
ASSERT RegisteelPokedexEntry.page4 - RegisteelPokedexEntry.page1 > 0 && RegisteelPokedexEntry.page4 - RegisteelPokedexEntry.page1 <= 255
	db RegisteelPokedexEntry.page2 - RegisteelPokedexEntry.page1, RegisteelPokedexEntry.page3 - RegisteelPokedexEntry.page1, RegisteelPokedexEntry.page4 - RegisteelPokedexEntry.page1
ASSERT KyogrePokedexEntry.page2 - KyogrePokedexEntry.page1 > 0 && KyogrePokedexEntry.page2 - KyogrePokedexEntry.page1 <= 255
ASSERT KyogrePokedexEntry.page3 - KyogrePokedexEntry.page1 > 0 && KyogrePokedexEntry.page3 - KyogrePokedexEntry.page1 <= 255
ASSERT KyogrePokedexEntry.page4 - KyogrePokedexEntry.page1 > 0 && KyogrePokedexEntry.page4 - KyogrePokedexEntry.page1 <= 255
	db KyogrePokedexEntry.page2 - KyogrePokedexEntry.page1, KyogrePokedexEntry.page3 - KyogrePokedexEntry.page1, KyogrePokedexEntry.page4 - KyogrePokedexEntry.page1
ASSERT GroudonPokedexEntry.page2 - GroudonPokedexEntry.page1 > 0 && GroudonPokedexEntry.page2 - GroudonPokedexEntry.page1 <= 255
ASSERT GroudonPokedexEntry.page3 - GroudonPokedexEntry.page1 > 0 && GroudonPokedexEntry.page3 - GroudonPokedexEntry.page1 <= 255
ASSERT GroudonPokedexEntry.page4 - GroudonPokedexEntry.page1 > 0 && GroudonPokedexEntry.page4 - GroudonPokedexEntry.page1 <= 255
	db GroudonPokedexEntry.page2 - GroudonPokedexEntry.page1, GroudonPokedexEntry.page3 - GroudonPokedexEntry.page1, GroudonPokedexEntry.page4 - GroudonPokedexEntry.page1
ASSERT RayquazaPokedexEntry.page2 - RayquazaPokedexEntry.page1 > 0 && RayquazaPokedexEntry.page2 - RayquazaPokedexEntry.page1 <= 255
ASSERT RayquazaPokedexEntry.page3 - RayquazaPokedexEntry.page1 > 0 && RayquazaPokedexEntry.page3 - RayquazaPokedexEntry.page1 <= 255
	db RayquazaPokedexEntry.page2 - RayquazaPokedexEntry.page1, RayquazaPokedexEntry.page3 - RayquazaPokedexEntry.page1, 0
ASSERT ShinxPokedexEntry.page2 - ShinxPokedexEntry.page1 > 0 && ShinxPokedexEntry.page2 - ShinxPokedexEntry.page1 <= 255
	db ShinxPokedexEntry.page2 - ShinxPokedexEntry.page1, 0, 0
ASSERT LuxioPokedexEntry.page2 - LuxioPokedexEntry.page1 > 0 && LuxioPokedexEntry.page2 - LuxioPokedexEntry.page1 <= 255
ASSERT LuxioPokedexEntry.page3 - LuxioPokedexEntry.page1 > 0 && LuxioPokedexEntry.page3 - LuxioPokedexEntry.page1 <= 255
	db LuxioPokedexEntry.page2 - LuxioPokedexEntry.page1, LuxioPokedexEntry.page3 - LuxioPokedexEntry.page1, 0
ASSERT LuxrayPokedexEntry.page2 - LuxrayPokedexEntry.page1 > 0 && LuxrayPokedexEntry.page2 - LuxrayPokedexEntry.page1 <= 255
	db LuxrayPokedexEntry.page2 - LuxrayPokedexEntry.page1, 0, 0
ASSERT CranidosPokedexEntry.page2 - CranidosPokedexEntry.page1 > 0 && CranidosPokedexEntry.page2 - CranidosPokedexEntry.page1 <= 255
	db CranidosPokedexEntry.page2 - CranidosPokedexEntry.page1, 0, 0
ASSERT RampardosPokedexEntry.page2 - RampardosPokedexEntry.page1 > 0 && RampardosPokedexEntry.page2 - RampardosPokedexEntry.page1 <= 255
	db RampardosPokedexEntry.page2 - RampardosPokedexEntry.page1, 0, 0
ASSERT ShieldonPokedexEntry.page2 - ShieldonPokedexEntry.page1 > 0 && ShieldonPokedexEntry.page2 - ShieldonPokedexEntry.page1 <= 255
ASSERT ShieldonPokedexEntry.page3 - ShieldonPokedexEntry.page1 > 0 && ShieldonPokedexEntry.page3 - ShieldonPokedexEntry.page1 <= 255
	db ShieldonPokedexEntry.page2 - ShieldonPokedexEntry.page1, ShieldonPokedexEntry.page3 - ShieldonPokedexEntry.page1, 0
ASSERT BastiodonPokedexEntry.page2 - BastiodonPokedexEntry.page1 > 0 && BastiodonPokedexEntry.page2 - BastiodonPokedexEntry.page1 <= 255
	db BastiodonPokedexEntry.page2 - BastiodonPokedexEntry.page1, 0, 0
ASSERT AmbipomPokedexEntry.page2 - AmbipomPokedexEntry.page1 > 0 && AmbipomPokedexEntry.page2 - AmbipomPokedexEntry.page1 <= 255
	db AmbipomPokedexEntry.page2 - AmbipomPokedexEntry.page1, 0, 0
ASSERT BunearyPokedexEntry.page2 - BunearyPokedexEntry.page1 > 0 && BunearyPokedexEntry.page2 - BunearyPokedexEntry.page1 <= 255
ASSERT BunearyPokedexEntry.page3 - BunearyPokedexEntry.page1 > 0 && BunearyPokedexEntry.page3 - BunearyPokedexEntry.page1 <= 255
	db BunearyPokedexEntry.page2 - BunearyPokedexEntry.page1, BunearyPokedexEntry.page3 - BunearyPokedexEntry.page1, 0
ASSERT LopunnyPokedexEntry.page2 - LopunnyPokedexEntry.page1 > 0 && LopunnyPokedexEntry.page2 - LopunnyPokedexEntry.page1 <= 255
	db LopunnyPokedexEntry.page2 - LopunnyPokedexEntry.page1, 0, 0
ASSERT MismagiusPokedexEntry.page2 - MismagiusPokedexEntry.page1 > 0 && MismagiusPokedexEntry.page2 - MismagiusPokedexEntry.page1 <= 255
ASSERT MismagiusPokedexEntry.page3 - MismagiusPokedexEntry.page1 > 0 && MismagiusPokedexEntry.page3 - MismagiusPokedexEntry.page1 <= 255
	db MismagiusPokedexEntry.page2 - MismagiusPokedexEntry.page1, MismagiusPokedexEntry.page3 - MismagiusPokedexEntry.page1, 0
ASSERT HonchkrowPokedexEntry.page2 - HonchkrowPokedexEntry.page1 > 0 && HonchkrowPokedexEntry.page2 - HonchkrowPokedexEntry.page1 <= 255
ASSERT HonchkrowPokedexEntry.page3 - HonchkrowPokedexEntry.page1 > 0 && HonchkrowPokedexEntry.page3 - HonchkrowPokedexEntry.page1 <= 255
	db HonchkrowPokedexEntry.page2 - HonchkrowPokedexEntry.page1, HonchkrowPokedexEntry.page3 - HonchkrowPokedexEntry.page1, 0
ASSERT BronzorPokedexEntry.page2 - BronzorPokedexEntry.page1 > 0 && BronzorPokedexEntry.page2 - BronzorPokedexEntry.page1 <= 255
	db BronzorPokedexEntry.page2 - BronzorPokedexEntry.page1, 0, 0
ASSERT BronzongPokedexEntry.page2 - BronzongPokedexEntry.page1 > 0 && BronzongPokedexEntry.page2 - BronzongPokedexEntry.page1 <= 255
ASSERT BronzongPokedexEntry.page3 - BronzongPokedexEntry.page1 > 0 && BronzongPokedexEntry.page3 - BronzongPokedexEntry.page1 <= 255
	db BronzongPokedexEntry.page2 - BronzongPokedexEntry.page1, BronzongPokedexEntry.page3 - BronzongPokedexEntry.page1, 0
ASSERT GiblePokedexEntry.page2 - GiblePokedexEntry.page1 > 0 && GiblePokedexEntry.page2 - GiblePokedexEntry.page1 <= 255
ASSERT GiblePokedexEntry.page3 - GiblePokedexEntry.page1 > 0 && GiblePokedexEntry.page3 - GiblePokedexEntry.page1 <= 255
	db GiblePokedexEntry.page2 - GiblePokedexEntry.page1, GiblePokedexEntry.page3 - GiblePokedexEntry.page1, 0
ASSERT GabitePokedexEntry.page2 - GabitePokedexEntry.page1 > 0 && GabitePokedexEntry.page2 - GabitePokedexEntry.page1 <= 255
	db GabitePokedexEntry.page2 - GabitePokedexEntry.page1, 0, 0
ASSERT GarchompPokedexEntry.page2 - GarchompPokedexEntry.page1 > 0 && GarchompPokedexEntry.page2 - GarchompPokedexEntry.page1 <= 255
ASSERT GarchompPokedexEntry.page3 - GarchompPokedexEntry.page1 > 0 && GarchompPokedexEntry.page3 - GarchompPokedexEntry.page1 <= 255
	db GarchompPokedexEntry.page2 - GarchompPokedexEntry.page1, GarchompPokedexEntry.page3 - GarchompPokedexEntry.page1, 0
ASSERT RioluPokedexEntry.page2 - RioluPokedexEntry.page1 > 0 && RioluPokedexEntry.page2 - RioluPokedexEntry.page1 <= 255
	db RioluPokedexEntry.page2 - RioluPokedexEntry.page1, 0, 0
ASSERT LucarioPokedexEntry.page2 - LucarioPokedexEntry.page1 > 0 && LucarioPokedexEntry.page2 - LucarioPokedexEntry.page1 <= 255
	db LucarioPokedexEntry.page2 - LucarioPokedexEntry.page1, 0, 0
ASSERT SkorupiPokedexEntry.page2 - SkorupiPokedexEntry.page1 > 0 && SkorupiPokedexEntry.page2 - SkorupiPokedexEntry.page1 <= 255
	db SkorupiPokedexEntry.page2 - SkorupiPokedexEntry.page1, 0, 0
ASSERT DrapionPokedexEntry.page2 - DrapionPokedexEntry.page1 > 0 && DrapionPokedexEntry.page2 - DrapionPokedexEntry.page1 <= 255
	db DrapionPokedexEntry.page2 - DrapionPokedexEntry.page1, 0, 0
ASSERT CroagunkPokedexEntry.page2 - CroagunkPokedexEntry.page1 > 0 && CroagunkPokedexEntry.page2 - CroagunkPokedexEntry.page1 <= 255
	db CroagunkPokedexEntry.page2 - CroagunkPokedexEntry.page1, 0, 0
ASSERT ToxicroakPokedexEntry.page2 - ToxicroakPokedexEntry.page1 > 0 && ToxicroakPokedexEntry.page2 - ToxicroakPokedexEntry.page1 <= 255
	db ToxicroakPokedexEntry.page2 - ToxicroakPokedexEntry.page1, 0, 0
ASSERT SnoverPokedexEntry.page2 - SnoverPokedexEntry.page1 > 0 && SnoverPokedexEntry.page2 - SnoverPokedexEntry.page1 <= 255
	db SnoverPokedexEntry.page2 - SnoverPokedexEntry.page1, 0, 0
ASSERT AbomasnowPokedexEntry.page2 - AbomasnowPokedexEntry.page1 > 0 && AbomasnowPokedexEntry.page2 - AbomasnowPokedexEntry.page1 <= 255
	db AbomasnowPokedexEntry.page2 - AbomasnowPokedexEntry.page1, 0, 0
ASSERT WeavilePokedexEntry.page2 - WeavilePokedexEntry.page1 > 0 && WeavilePokedexEntry.page2 - WeavilePokedexEntry.page1 <= 255
	db WeavilePokedexEntry.page2 - WeavilePokedexEntry.page1, 0, 0
ASSERT MagnezonePokedexEntry.page2 - MagnezonePokedexEntry.page1 > 0 && MagnezonePokedexEntry.page2 - MagnezonePokedexEntry.page1 <= 255
	db MagnezonePokedexEntry.page2 - MagnezonePokedexEntry.page1, 0, 0
ASSERT LickilickyPokedexEntry.page2 - LickilickyPokedexEntry.page1 > 0 && LickilickyPokedexEntry.page2 - LickilickyPokedexEntry.page1 <= 255
	db LickilickyPokedexEntry.page2 - LickilickyPokedexEntry.page1, 0, 0
ASSERT RhyperiorPokedexEntry.page2 - RhyperiorPokedexEntry.page1 > 0 && RhyperiorPokedexEntry.page2 - RhyperiorPokedexEntry.page1 <= 255
ASSERT RhyperiorPokedexEntry.page3 - RhyperiorPokedexEntry.page1 > 0 && RhyperiorPokedexEntry.page3 - RhyperiorPokedexEntry.page1 <= 255
	db RhyperiorPokedexEntry.page2 - RhyperiorPokedexEntry.page1, RhyperiorPokedexEntry.page3 - RhyperiorPokedexEntry.page1, 0
ASSERT TangrowthPokedexEntry.page2 - TangrowthPokedexEntry.page1 > 0 && TangrowthPokedexEntry.page2 - TangrowthPokedexEntry.page1 <= 255
	db TangrowthPokedexEntry.page2 - TangrowthPokedexEntry.page1, 0, 0
ASSERT TogekissPokedexEntry.page2 - TogekissPokedexEntry.page1 > 0 && TogekissPokedexEntry.page2 - TogekissPokedexEntry.page1 <= 255
	db TogekissPokedexEntry.page2 - TogekissPokedexEntry.page1, 0, 0
ASSERT YanmegaPokedexEntry.page2 - YanmegaPokedexEntry.page1 > 0 && YanmegaPokedexEntry.page2 - YanmegaPokedexEntry.page1 <= 255
	db YanmegaPokedexEntry.page2 - YanmegaPokedexEntry.page1, 0, 0
ASSERT LeafeonPokedexEntry.page2 - LeafeonPokedexEntry.page1 > 0 && LeafeonPokedexEntry.page2 - LeafeonPokedexEntry.page1 <= 255
	db LeafeonPokedexEntry.page2 - LeafeonPokedexEntry.page1, 0, 0
ASSERT GlaceonPokedexEntry.page2 - GlaceonPokedexEntry.page1 > 0 && GlaceonPokedexEntry.page2 - GlaceonPokedexEntry.page1 <= 255
ASSERT GlaceonPokedexEntry.page3 - GlaceonPokedexEntry.page1 > 0 && GlaceonPokedexEntry.page3 - GlaceonPokedexEntry.page1 <= 255
	db GlaceonPokedexEntry.page2 - GlaceonPokedexEntry.page1, GlaceonPokedexEntry.page3 - GlaceonPokedexEntry.page1, 0
ASSERT GliscorPokedexEntry.page2 - GliscorPokedexEntry.page1 > 0 && GliscorPokedexEntry.page2 - GliscorPokedexEntry.page1 <= 255
ASSERT GliscorPokedexEntry.page3 - GliscorPokedexEntry.page1 > 0 && GliscorPokedexEntry.page3 - GliscorPokedexEntry.page1 <= 255
	db GliscorPokedexEntry.page2 - GliscorPokedexEntry.page1, GliscorPokedexEntry.page3 - GliscorPokedexEntry.page1, 0
ASSERT MamoswinePokedexEntry.page2 - MamoswinePokedexEntry.page1 > 0 && MamoswinePokedexEntry.page2 - MamoswinePokedexEntry.page1 <= 255
	db MamoswinePokedexEntry.page2 - MamoswinePokedexEntry.page1, 0, 0
ASSERT PorygonZPokedexEntry.page2 - PorygonZPokedexEntry.page1 > 0 && PorygonZPokedexEntry.page2 - PorygonZPokedexEntry.page1 <= 255
	db PorygonZPokedexEntry.page2 - PorygonZPokedexEntry.page1, 0, 0
ASSERT RegigigasPokedexEntry.page2 - RegigigasPokedexEntry.page1 > 0 && RegigigasPokedexEntry.page2 - RegigigasPokedexEntry.page1 <= 255
	db RegigigasPokedexEntry.page2 - RegigigasPokedexEntry.page1, 0, 0
ASSERT @ - PokedexDescriptionPageOffsets == (NUM_POKEMON - TREECKO + 1) * 3
