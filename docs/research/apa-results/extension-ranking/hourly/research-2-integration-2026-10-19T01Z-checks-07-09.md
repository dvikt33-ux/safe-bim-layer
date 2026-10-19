# APA №2 01Z — проверки 07–09: SDK29 LibraryManager
Graphisoft DevKit tag 29.3100, EULA, не SDK30. Источник: https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_library_1_1_library.html ; https://graphisoft.github.io/archicad-api-devkit/class_a_c_a_p_i_1_1_library_1_1_library_manager.html

07. Вопрос: может ли SDK читать без PLN? `GetLibraryManager()` возвращает `Result<LibraryManager>`, без открытого плана `APIERR_NOPLAN`. Нужен native read-only Bridge; прямой Python binding NOT_FOUND. Далее зависимости.
08. Вопрос: готовый .libpack dependency graph? Library:203 `GetPackageDependencies(): Result<vector<tuple<GS::UniString,GS::Guid,UInt32>>>` = name,package ID,subversion. C++ SOURCE, JSON adapter NOT_FOUND. Далее минимальная сборка.
09. Вопрос: проверка AC29? Library:197–203 `GetPackageMinACVersion()`, `GetPackageMinACBuildNumber()` дают UInt32; сравнить с 29/5101, но только после `IsPackage()`. Далее GSM.
