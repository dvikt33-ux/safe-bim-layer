# APA №2 04Z — проверки 19–22

19. Tapir1.5.9 CreateWindows: windowsData требует ownerWallId и centerOffset≥0; width,height>0, favoriteName optional. REUSE; далее host.
20. CreateDoors: doorsData имеет аналогичный контракт, плюс orientation flags. REUSE; далее door fixture.
21. GetDetailsOfElements Wall: geometryType, beg/end, arcAngle, floorIndex, height, referenceLineLocation. REUSE; PDF→wall resolver NOT_FOUND.
22. PR556/release1.5.9: marker defaults сохраняются, factory fallback при пустых params. Далее readback stamp.
