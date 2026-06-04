---
name: dv-generate
description: Generate source-controlled Dataverse solution XML files (customizations.xml, solution.xml, pack.sh) without a live environment. Use when the user wants to create a new solution from scratch, add tables/fields/views/forms, or scaffold a model-driven app with AppModule and SiteMap. Always ask for the publisher prefix before generating any XML.
---

# Skill: Dataverse Solution Generation (Source-Controlled XML)

Generate zip-importable Power Platform solutions from plain XML files on disk. No live environment required during authoring. Import via `pac solution import` or make.powerapps.com.

---

## Publisher prefix — ask first

**Always confirm the publisher prefix before generating any XML.** The prefix is prepended to every table, column, option set, app, and site map schema name. It is set once per publisher and cannot be changed after components are created.

Ask the user:
> "What publisher prefix should I use? (e.g., `contoso`, `sa`, `lit` — 2–8 lowercase letters, no numbers or hyphens)"

Then substitute `{{prefix}}_` everywhere in the templates below.

**Never use `new_`** — it is the default Microsoft prefix and causes naming collisions.

The publisher block in `solution.xml` also needs:
- `<UniqueName>` — a PascalCase identifier for the publisher (e.g., `ContosoInc`)
- `<CustomizationPrefix>` — the lowercase prefix (e.g., `contoso`)
- `<CustomizationOptionValuePrefix>` — a unique integer (e.g., `10000`); must not clash with other publishers in the same environment

---

## Skill boundaries

| Need | Use instead |
|---|---|
| Export/import/pack/unpack via PAC CLI | **dv-solution** |
| Query or read Dataverse records | **dv-query** |
| Create/update records via API | **dv-data** |
| Connect to Dataverse / configure auth | **dv-connect** |

---

## File Structure

Every importable solution zip contains exactly **three files at the zip root** (no subdirectory):

```
[Content_Types].xml
solution.xml
customizations.xml
```

Pack with:
```bash
cd MySolutionDir
zip -j ../MySolution.zip "[Content_Types].xml" solution.xml customizations.xml
```

### [Content_Types].xml (static — always identical)

```xml
<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/octet-stream" />
</Types>
```

---

## solution.xml

The root `<ImportExportXml>` element **must** include all version attributes shown — omitting any causes import failure.

```xml
<ImportExportXml version="9.2.26044.164" SolutionPackageVersion="9.2" languagecode="1033"
    generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    OrganizationVersion="9.2.26044.164" OrganizationSchemaType="Standard"
    CRMServerServiceabilityVersion="9.2.26044.00164">
  <SolutionManifest>
    <UniqueName>{{SolutionUniqueName}}</UniqueName>
    <LocalizedNames>
      <LocalizedName description="{{Solution Display Name}}" languagecode="1033" />
    </LocalizedNames>
    <Descriptions/>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>{{PublisherUniqueName}}</UniqueName>
      <LocalizedNames>
        <LocalizedName description="{{Publisher Display Name}}" languagecode="1033" />
      </LocalizedNames>
      <Descriptions/>
      <EMailAddress>{{publisher@email.com}}</EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>{{prefix}}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>{{OptionValuePrefix}}</CustomizationOptionValuePrefix>
      <Addresses>
        <Address>
          <AddressNumber>1</AddressNumber><AddressTypeCode>1</AddressTypeCode>
          <City xsi:nil="true"></City><County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country><Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude><Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2><Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude><Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode><PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode>1</ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1><Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone><UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>
        <Address>
          <AddressNumber>2</AddressNumber><AddressTypeCode>1</AddressTypeCode>
          <City xsi:nil="true"></City><County xsi:nil="true"></County>
          <Country xsi:nil="true"></Country><Fax xsi:nil="true"></Fax>
          <FreightTermsCode xsi:nil="true"></FreightTermsCode>
          <ImportSequenceNumber xsi:nil="true"></ImportSequenceNumber>
          <Latitude xsi:nil="true"></Latitude><Line1 xsi:nil="true"></Line1>
          <Line2 xsi:nil="true"></Line2><Line3 xsi:nil="true"></Line3>
          <Longitude xsi:nil="true"></Longitude><Name xsi:nil="true"></Name>
          <PostalCode xsi:nil="true"></PostalCode><PostOfficeBox xsi:nil="true"></PostOfficeBox>
          <PrimaryContactName xsi:nil="true"></PrimaryContactName>
          <ShippingMethodCode>1</ShippingMethodCode>
          <StateOrProvince xsi:nil="true"></StateOrProvince>
          <Telephone1 xsi:nil="true"></Telephone1><Telephone2 xsi:nil="true"></Telephone2>
          <Telephone3 xsi:nil="true"></Telephone3>
          <TimeZoneRuleVersionNumber xsi:nil="true"></TimeZoneRuleVersionNumber>
          <UPSZone xsi:nil="true"></UPSZone><UTCOffset xsi:nil="true"></UTCOffset>
          <UTCConversionTimeZoneCode xsi:nil="true"></UTCConversionTimeZoneCode>
        </Address>
      </Addresses>
    </Publisher>
    <RootComponents>
      <!-- One entry per entity: type="1" -->
      <RootComponent type="1" schemaName="{{prefix}}_{{entity}}" behavior="0" />
      <!-- If including a model-driven app: -->
      <RootComponent type="62" schemaName="{{prefix}}_{{appname}}" behavior="0" />
      <RootComponent type="80" schemaName="{{prefix}}_{{appname}}" behavior="0" />
    </RootComponents>
    <!-- Required when solution includes an AppModule -->
    <MissingDependencies>
      <MissingDependency>
        <Required type="61" schemaName="msdyn_/Images/AppModule_Default_Icon.png"
            displayName="msdyn_/Images/AppModule_Default_Icon.png"
            solution="AppModuleWebResources (2.5)">
          <package appName="AppModule Web Resources Package" version="2.5">AppModuleWebResources (2.5)</package>
        </Required>
        <Dependent type="80" schemaName="{{prefix}}_{{appname}}" displayName="{{App Display Name}}" />
      </MissingDependency>
      <MissingDependency>
        <Required type="SettingDefinition" displayName="AppChannel"
            solution="msdyn_AppFrameworkInfraExtensions (1.0.0.16)"
            id.uniquename="AppChannel">
          <package appName="PowerAppsAppFramework Package" version="1.0.0.25">PowerAppsAppFramework_Anchor (1.0.0.25)</package>
        </Required>
        <Dependent type="AppSetting"
            displayName="parentappmoduleid.uniquename={{prefix}}_{{appname}},settingdefinitionid.uniquename=AppChannel"
            id.parentappmoduleid.uniquename="{{prefix}}_{{appname}}"
            id.settingdefinitionid.uniquename="AppChannel" />
      </MissingDependency>
    </MissingDependencies>
  </SolutionManifest>
</ImportExportXml>
```

---

## customizations.xml

### Root and top-level structure

`<attributes>` must come **before** entity-level properties (`<EntitySetName>`, `<OwnershipTypeMask>`, etc.) inside `<entity>`.

```xml
<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    OrganizationVersion="9.2.26044.164" OrganizationSchemaType="Standard"
    CRMServerServiceabilityVersion="9.2.26044.00164">
  <Entities>
    <!-- Entity blocks go here, one per table -->
  </Entities>
  <optionsets />
  <CustomControls />
  <EntityDataProviders />
  <Languages><Language>1033</Language></Languages>
  <!-- AppModuleSiteMaps and AppModules go here (after Languages) if including an app -->
</ImportExportXml>
```

### Entity block

```xml
<Entity>
  <Name LocalizedName="{{Display Name}}" OriginalName="{{Display Name}}">{{prefix}}_{{entity}}</Name>
  <EntityInfo>
    <entity Name="{{prefix}}_{{entity}}">
      <LocalizedNames><LocalizedName description="{{Display Name}}" languagecode="1033" /></LocalizedNames>
      <LocalizedCollectionNames><LocalizedCollectionName description="{{Plural Name}}" languagecode="1033" /></LocalizedCollectionNames>
      <Descriptions><Description description="" languagecode="1033" /></Descriptions>
      <attributes>
        <!-- ALL attribute elements go here FIRST -->
      </attributes>
      <EntitySetName>{{prefix}}_{{entities}}</EntitySetName>
      <IsDuplicateCheckSupported>1</IsDuplicateCheckSupported>
      <IsBusinessProcessEnabled>0</IsBusinessProcessEnabled>
      <IsRequiredOffline>0</IsRequiredOffline>
      <IsInteractionCentricEnabled>0</IsInteractionCentricEnabled>
      <IsCollaboration>0</IsCollaboration>
      <AutoRouteToOwnerQueue>0</AutoRouteToOwnerQueue>
      <IsConnectionsEnabled>0</IsConnectionsEnabled>
      <EntityColor></EntityColor>
      <IsDocumentManagementEnabled>0</IsDocumentManagementEnabled>
      <AutoCreateAccessTeams>0</AutoCreateAccessTeams>
      <IsOneNoteIntegrationEnabled>0</IsOneNoteIntegrationEnabled>
      <IsKnowledgeManagementEnabled>0</IsKnowledgeManagementEnabled>
      <IsSLAEnabled>0</IsSLAEnabled>
      <IsDocumentRecommendationsEnabled>0</IsDocumentRecommendationsEnabled>
      <IsBPFEntity>0</IsBPFEntity>
      <OwnershipTypeMask>UserOwned</OwnershipTypeMask>
      <IsAuditEnabled>0</IsAuditEnabled>
      <IsRetrieveAuditEnabled>0</IsRetrieveAuditEnabled>
      <IsRetrieveMultipleAuditEnabled>0</IsRetrieveMultipleAuditEnabled>
      <IsActivity>0</IsActivity><ActivityTypeMask></ActivityTypeMask><IsActivityParty>0</IsActivityParty>
      <IsReplicated>0</IsReplicated><IsReplicationUserFiltered>0</IsReplicationUserFiltered>
      <IsMailMergeEnabled>1</IsMailMergeEnabled>
      <IsVisibleInMobile>0</IsVisibleInMobile>
      <IsVisibleInMobileClient>0</IsVisibleInMobileClient>
      <IsReadOnlyInMobileClient>0</IsReadOnlyInMobileClient>
      <IsOfflineInMobileClient>1</IsOfflineInMobileClient>
      <DaysSinceRecordLastModified>0</DaysSinceRecordLastModified>
      <MobileOfflineFilters></MobileOfflineFilters>
      <IsMapiGridEnabled>1</IsMapiGridEnabled>
      <IsReadingPaneEnabled>1</IsReadingPaneEnabled>
      <IsQuickCreateEnabled>0</IsQuickCreateEnabled>
      <SyncToExternalSearchIndex>0</SyncToExternalSearchIndex>
      <IntroducedVersion>1.0</IntroducedVersion>
      <IsCustomizable>1</IsCustomizable>
      <IsRenameable>1</IsRenameable>
      <IsMappable>1</IsMappable>
      <CanModifyAuditSettings>1</CanModifyAuditSettings>
      <CanModifyMobileVisibility>1</CanModifyMobileVisibility>
      <CanModifyMobileClientVisibility>1</CanModifyMobileClientVisibility>
      <CanModifyMobileClientReadOnly>1</CanModifyMobileClientReadOnly>
      <CanModifyMobileClientOffline>1</CanModifyMobileClientOffline>
      <CanModifyConnectionSettings>1</CanModifyConnectionSettings>
      <CanModifyDuplicateDetectionSettings>1</CanModifyDuplicateDetectionSettings>
      <CanModifyMailMergeSettings>1</CanModifyMailMergeSettings>
      <CanModifyQueueSettings>1</CanModifyQueueSettings>
      <CanCreateAttributes>1</CanCreateAttributes>
      <CanCreateForms>1</CanCreateForms>
      <CanCreateCharts>1</CanCreateCharts>
      <CanCreateViews>1</CanCreateViews>
      <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings>
      <CanEnableSyncToExternalSearchIndex>1</CanEnableSyncToExternalSearchIndex>
      <EnforceStateTransitions>0</EnforceStateTransitions>
      <CanChangeHierarchicalRelationship>1</CanChangeHierarchicalRelationship>
      <EntityHelpUrlEnabled>0</EntityHelpUrlEnabled>
      <ChangeTrackingEnabled>1</ChangeTrackingEnabled>
      <CanChangeTrackingBeEnabled>1</CanChangeTrackingBeEnabled>
      <IsEnabledForExternalChannels>0</IsEnabledForExternalChannels>
      <IsMSTeamsIntegrationEnabled>0</IsMSTeamsIntegrationEnabled>
      <IsSolutionAware>0</IsSolutionAware>
    </entity>
  </EntityInfo>
  <RibbonDiffXml>
    <CustomActions />
    <Templates><RibbonTemplates Id="Mscrm.Templates"></RibbonTemplates></Templates>
    <CommandDefinitions />
    <RuleDefinitions><TabDisplayRules /><DisplayRules /><EnableRules /></RuleDefinitions>
    <LocLabels />
  </RibbonDiffXml>
  <FormXml><!-- see Form Template below --></FormXml>
  <SavedQueries><!-- see View Templates below --></SavedQueries>
</Entity>
```

**Do NOT include system attributes** (`statecode`, `statuscode`, `createdon`, `modifiedon`, `ownerid`, etc.) — Dataverse auto-creates them. Including them causes a duplicate key import error.

---

## Attribute Templates

All attributes share the same scaffold. Key rules:
- Boolean-like properties must use **simple integers** — NOT compound `<Value>/<CanModify>` blocks (which cause "string '11' is not a valid Boolean value" errors)
- Display labels use `<displaynames>/<displayname>` (lowercase, no "Localized" prefix)
- `ImeMode` is a string: `auto`, `inactive`, or `disabled` (not an integer)

### Text (nvarchar) — short text

```xml
<attribute PhysicalName="{{prefix}}_{{fieldname}}">
  <Type>nvarchar</Type><Name>{{prefix}}_{{fieldname}}</Name><LogicalName>{{prefix}}_{{fieldname}}</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>auto</ImeMode>
  <ValidForUpdateApi>1</ValidForUpdateApi><ValidForReadApi>1</ValidForReadApi><ValidForCreateApi>1</ValidForCreateApi>
  <IsCustomField>1</IsCustomField><IsAuditEnabled>1</IsAuditEnabled><IsSecured>0</IsSecured>
  <IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings><CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings><SourceType>0</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled><IsSortableEnabled>0</IsSortableEnabled>
  <CanModifyGlobalFilterSettings>1</CanModifyGlobalFilterSettings><CanModifyIsSortableSettings>1</CanModifyIsSortableSettings>
  <IsDataSourceSecret>0</IsDataSourceSecret><AutoNumberFormat></AutoNumberFormat>
  <IsSearchable>0</IsSearchable><IsFilterable>0</IsFilterable><IsRetrievable>0</IsRetrievable><IsLocalizable>0</IsLocalizable>
  <Format>text</Format><MaxLength>100</MaxLength><Length>200</Length>
  <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
  <Descriptions><Description description="" languagecode="1033" /></Descriptions>
</attribute>
```

**Primary name field** — add `PrimaryName` to `DisplayMask`:
```xml
<DisplayMask>PrimaryName|ValidForAdvancedFind|ValidForForm|ValidForGrid|RequiredForForm</DisplayMask>
```

### Multiline text

Use `<Type>nvarchar</Type>` + `<Format>textarea</Format>`. **`<Type>memo</Type>` is not recognised.**

```xml
<Format>textarea</Format><MaxLength>2000</MaxLength><Length>4000</Length>
```

### Decimal / Currency

```xml
<attribute PhysicalName="{{prefix}}_{{fieldname}}">
  <Type>decimal</Type><Name>{{prefix}}_{{fieldname}}</Name><LogicalName>{{prefix}}_{{fieldname}}</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>inactive</ImeMode>
  <ValidForUpdateApi>1</ValidForUpdateApi><ValidForReadApi>1</ValidForReadApi><ValidForCreateApi>1</ValidForCreateApi>
  <IsCustomField>1</IsCustomField><IsAuditEnabled>1</IsAuditEnabled><IsSecured>0</IsSecured>
  <IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings><CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings><SourceType>0</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled><IsSortableEnabled>0</IsSortableEnabled>
  <CanModifyGlobalFilterSettings>1</CanModifyGlobalFilterSettings><CanModifyIsSortableSettings>1</CanModifyIsSortableSettings>
  <IsDataSourceSecret>0</IsDataSourceSecret><AutoNumberFormat></AutoNumberFormat>
  <IsSearchable>0</IsSearchable><IsFilterable>1</IsFilterable><IsRetrievable>1</IsRetrievable><IsLocalizable>0</IsLocalizable>
  <Precision>2</Precision><MinValue>-100000000000</MinValue><MaxValue>100000000000</MaxValue>
  <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
  <Descriptions><Description description="" languagecode="1033" /></Descriptions>
</attribute>
```

For non-negative amounts (e.g., Debit Amount): `<MinValue>0</MinValue>`.

### Integer

Replace the precision/min/max block with:
```xml
<Type>int</Type>
...
<MinValue>-2147483648</MinValue><MaxValue>2147483647</MaxValue>
```

### Date / DateTime

```xml
<Type>datetime</Type>
...
<ImeMode>inactive</ImeMode>
<Format>date</Format>   <!-- or: datetime -->
```

### Picklist (option set)

Option values start at `100000000` (publisher option prefix `10000` × 10000).

```xml
<attribute PhysicalName="{{prefix}}_{{fieldname}}">
  <Type>picklist</Type><Name>{{prefix}}_{{fieldname}}</Name><LogicalName>{{prefix}}_{{fieldname}}</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>auto</ImeMode>
  <ValidForUpdateApi>1</ValidForUpdateApi><ValidForReadApi>1</ValidForReadApi><ValidForCreateApi>1</ValidForCreateApi>
  <IsCustomField>1</IsCustomField><IsAuditEnabled>1</IsAuditEnabled><IsSecured>0</IsSecured>
  <IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings><CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings><SourceType>0</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled><IsSortableEnabled>0</IsSortableEnabled>
  <CanModifyGlobalFilterSettings>1</CanModifyGlobalFilterSettings><CanModifyIsSortableSettings>1</CanModifyIsSortableSettings>
  <IsDataSourceSecret>0</IsDataSourceSecret><AutoNumberFormat></AutoNumberFormat>
  <IsSearchable>0</IsSearchable><IsFilterable>1</IsFilterable><IsRetrievable>1</IsRetrievable><IsLocalizable>0</IsLocalizable>
  <optionset Name="{{prefix}}_{{fieldname}}">
    <OptionSetType>picklist</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>
    <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
    <Descriptions><Description description="" languagecode="1033" /></Descriptions>
    <options>
      <option value="100000000"><labels><label description="Option A" languagecode="1033" /></labels><Descriptions><Description description="" languagecode="1033" /></Descriptions></option>
      <option value="100000001"><labels><label description="Option B" languagecode="1033" /></labels><Descriptions><Description description="" languagecode="1033" /></Descriptions></option>
    </options>
  </optionset>
  <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
  <Descriptions><Description description="" languagecode="1033" /></Descriptions>
</attribute>
```

**Option labels** = lowercase `<labels>/<label>`. NOT `<Labels>/<Label>`.

### Boolean (Two Options)

**Attribute `<Type>` = `bit`. Optionset `<OptionSetType>` = `bool`. These are different — do not swap them.**

**`<DefaultValue>0</DefaultValue>` is required** (placed just before `<optionset>`). Without it the field renders as read-only in the form.

```xml
<attribute PhysicalName="{{prefix}}_{{fieldname}}">
  <Type>bit</Type><Name>{{prefix}}_{{fieldname}}</Name><LogicalName>{{prefix}}_{{fieldname}}</LogicalName>
  <RequiredLevel>none</RequiredLevel>
  <DisplayMask>ValidForAdvancedFind|ValidForForm|ValidForGrid</DisplayMask>
  <ImeMode>auto</ImeMode>
  <ValidForUpdateApi>1</ValidForUpdateApi><ValidForReadApi>1</ValidForReadApi><ValidForCreateApi>1</ValidForCreateApi>
  <IsCustomField>1</IsCustomField><IsAuditEnabled>1</IsAuditEnabled><IsSecured>0</IsSecured>
  <IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><IsRenameable>1</IsRenameable>
  <CanModifySearchSettings>1</CanModifySearchSettings><CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>
  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings><SourceType>0</SourceType>
  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled><IsSortableEnabled>0</IsSortableEnabled>
  <CanModifyGlobalFilterSettings>1</CanModifyGlobalFilterSettings><CanModifyIsSortableSettings>1</CanModifyIsSortableSettings>
  <IsDataSourceSecret>0</IsDataSourceSecret><AutoNumberFormat></AutoNumberFormat>
  <IsSearchable>0</IsSearchable><IsFilterable>1</IsFilterable><IsRetrievable>1</IsRetrievable><IsLocalizable>0</IsLocalizable>
  <DefaultValue>0</DefaultValue>
  <optionset Name="{{prefix}}_{{fieldname}}">
    <OptionSetType>bool</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>
    <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
    <Descriptions><Description description="" languagecode="1033" /></Descriptions>
    <TrueOption><labels><label description="Yes" languagecode="1033" /></labels><Descriptions><Description description="" languagecode="1033" /></Descriptions></TrueOption>
    <FalseOption><labels><label description="No" languagecode="1033" /></labels><Descriptions><Description description="" languagecode="1033" /></Descriptions></FalseOption>
  </optionset>
  <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
  <Descriptions><Description description="" languagecode="1033" /></Descriptions>
</attribute>
```

---

## View Templates

Every entity needs at minimum: a default list view (`querytype 0`) and a Quick Find view (`querytype 4`).

**`returnedtypecode`** = entity logical name string (`{{prefix}}_todo`), **not a number**.

**GUIDs must be fresh per import attempt.** Failed-import GUIDs persist in the environment and cause re-import to fail. Generate:
```bash
python3 -c "import uuid; print(str(uuid.uuid4()).upper())"
```

For readability, use sequential-looking hex GUIDs like `{B1000001-0000-4000-8000-000000000001}` — group entities by first digit (`B1` = entity 1, `B2` = entity 2, etc.).

```xml
<SavedQueries>
  <!-- Default list view -->
  <savedquery>
    <savedqueryid>{UNIQUE-GUID-1}</savedqueryid>
    <querytype>0</querytype>
    <name>All {{Plural Name}}</name>
    <returnedtypecode>{{prefix}}_{{entity}}</returnedtypecode>
    <isdefault>1</isdefault><iscustom>1</iscustom><isquickfindquery>0</isquickfindquery>
    <IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>
    <columnsetxml><columnset>
      <column name="{{prefix}}_{{field1}}"/><column name="{{prefix}}_{{field2}}"/>
    </columnset></columnsetxml>
    <layoutxml><grid name="resultset" object="{{prefix}}_{{entity}}" jump="{{prefix}}_{{primaryfield}}" select="1" preview="0" icon="1">
      <row name="result" id="{{prefix}}_{{entity}}id">
        <cell name="{{prefix}}_{{field1}}" width="200"/>
        <cell name="{{prefix}}_{{field2}}" width="150"/>
      </row>
    </grid></layoutxml>
    <fetchxml><fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
      <entity name="{{prefix}}_{{entity}}">
        <attribute name="{{prefix}}_{{field1}}"/>
        <attribute name="{{prefix}}_{{field2}}"/>
        <attribute name="{{prefix}}_{{entity}}id"/>
        <order attribute="{{prefix}}_{{primaryfield}}" descending="false"/>
        <filter type="and"><condition attribute="statecode" operator="eq" value="0"/></filter>
      </entity>
    </fetch></fetchxml>
    <LocalizedNames><LocalizedName description="All {{Plural Name}}" languagecode="1033"/></LocalizedNames>
    <Descriptions><Description description="" languagecode="1033"/></Descriptions>
  </savedquery>

  <!-- Quick Find view -->
  <savedquery>
    <savedqueryid>{UNIQUE-GUID-2}</savedqueryid>
    <querytype>4</querytype>
    <name>Quick Find {{Plural Name}}</name>
    <returnedtypecode>{{prefix}}_{{entity}}</returnedtypecode>
    <isdefault>1</isdefault><iscustom>1</iscustom><isquickfindquery>1</isquickfindquery>
    <IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>
    <columnsetxml><columnset>
      <column name="{{prefix}}_{{field1}}"/><column name="{{prefix}}_{{field2}}"/>
    </columnset></columnsetxml>
    <layoutxml><grid name="resultset" object="{{prefix}}_{{entity}}" jump="{{prefix}}_{{primaryfield}}" select="1" preview="0" icon="1">
      <row name="result" id="{{prefix}}_{{entity}}id">
        <cell name="{{prefix}}_{{field1}}" width="200"/>
        <cell name="{{prefix}}_{{field2}}" width="150"/>
      </row>
    </grid></layoutxml>
    <fetchxml><fetch version="1.0" output-format="xml-platform" mapping="logical" distinct="false">
      <entity name="{{prefix}}_{{entity}}">
        <attribute name="{{prefix}}_{{field1}}"/>
        <attribute name="{{prefix}}_{{field2}}"/>
        <attribute name="{{prefix}}_{{entity}}id"/>
        <order attribute="{{prefix}}_{{primaryfield}}" descending="false"/>
        <filter type="and"><condition attribute="statecode" operator="eq" value="0"/></filter>
      </entity>
    </fetch></fetchxml>
    <LocalizedNames><LocalizedName description="Quick Find {{Plural Name}}" languagecode="1033"/></LocalizedNames>
    <Descriptions><Description description="" languagecode="1033"/></Descriptions>
  </savedquery>
</SavedQueries>
```

---

## Form Template

Form, tab, section, and cell GUIDs must all be unique. Use sequential GUIDs (e.g., `{A1000001-0000-4000-8000-000000000001}` for form, `{A1000002...}` for tab, etc.) — group by entity number for readability.

**Control classids by field type:**

| Type | classid |
|---|---|
| Text (nvarchar) | `{4273EDBD-AC1D-40d3-9FB2-095C621B552D}` |
| Picklist | `{3EF39988-22BB-4f0b-BBBE-64B5A3748AEE}` |
| Decimal / Integer | `{C3EFE0C3-0EC6-42be-8349-CBD9079C717A}` |
| Boolean | `{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}` |
| DateTime | `{5D68B988-0661-4db2-BC3E-17598AD3BE6C}` |
| Owner lookup (system) | `{270BD3DB-D9AF-4782-9025-509E298DEC0A}` |

```xml
<FormXml>
  <forms type="main">
    <systemform>
      <formid>{A1000001-0000-4000-8000-000000000001}</formid>
      <IntroducedVersion>1.0</IntroducedVersion>
      <FormPresentation>1</FormPresentation>
      <FormActivationState>1</FormActivationState>
      <form>
        <tabs>
          <tab verticallayout="true" id="{A1000002-0000-4000-8000-000000000001}" IsUserDefined="1">
            <labels><label description="General" languagecode="1033" /></labels>
            <columns><column width="100%"><sections>
              <section showlabel="false" showbar="false" IsUserDefined="0" id="{A1000003-0000-4000-8000-000000000001}">
                <labels><label description="General" languagecode="1033" /></labels>
                <rows>
                  <row><cell id="{A1000011-0000-4000-8000-000000000001}">
                    <labels><label description="{{Label}}" languagecode="1033" /></labels>
                    <control id="{{prefix}}_{{field}}" classid="{4273EDBD-AC1D-40d3-9FB2-095C621B552D}" datafieldname="{{prefix}}_{{field}}" />
                  </cell></row>
                  <!-- repeat <row> for each field; increment last segment: ...0011, ...0012, ... -->
                  <row><cell id="{A1000099-0000-4000-8000-000000000001}">
                    <labels><label description="Owner" languagecode="1033" /></labels>
                    <control id="ownerid" classid="{270BD3DB-D9AF-4782-9025-509E298DEC0A}" datafieldname="ownerid" />
                  </cell></row>
                </rows>
              </section>
            </sections></column></columns>
          </tab>
        </tabs>
      </form>
      <IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>
      <LocalizedNames><LocalizedName description="Information" languagecode="1033" /></LocalizedNames>
      <Descriptions><Description description="" languagecode="1033" /></Descriptions>
    </systemform>
  </forms>
</FormXml>
```

---

## AppModule + SiteMap

Place after `<Languages>` in customizations.xml, before `</ImportExportXml>`.

**Rules:**
- `<SubArea>` is self-closing with `Icon="/_imgs/imagestrips/transparent_spacer.gif"` — no `<Titles>` child element.
- `<WebResourceId>953b9fac-1e5e-e611-80d6-00155ded156f</WebResourceId>` — system default app icon, same GUID in every solution.
- `<ClientType>4</ClientType>` — required for Unified Interface.
- `<appsettings>` with `AppChannel=1` is required.
- `<AppModuleComponents>` and `<AppModuleRoleMaps />` are child elements (not XML attributes).

```xml
<AppModuleSiteMaps>
  <AppModuleSiteMap>
    <SiteMapUniqueName>{{prefix}}_{{appname}}</SiteMapUniqueName>
    <EnableCollapsibleGroups>False</EnableCollapsibleGroups>
    <ShowHome>True</ShowHome><ShowPinned>True</ShowPinned><ShowRecents>True</ShowRecents>
    <SiteMap IntroducedVersion="7.0.0.0">
      <Area Id="area_{{prefix}}_{{entity}}" ResourceId="SitemapDesigner.NewTitle" DescriptionResourceId="SitemapDesigner.NewTitle" ShowGroups="true" IntroducedVersion="7.0.0.0">
        <Titles><Title LCID="1033" Title="{{Area Title}}" /></Titles>
        <Group Id="group_{{prefix}}_{{entity}}" ResourceId="SitemapDesigner.NewGroup" DescriptionResourceId="SitemapDesigner.NewGroup" IntroducedVersion="7.0.0.0" IsProfile="false" ToolTipResourseId="SitemapDesigner.Unknown">
          <SubArea Id="subarea_{{prefix}}_{{entity}}" Icon="/_imgs/imagestrips/transparent_spacer.gif" Entity="{{prefix}}_{{entity}}" Client="All,Outlook,OutlookLaptopClient,OutlookWorkstationClient,Web" AvailableOffline="true" PassParams="false" Sku="All,OnPremise,Live,SPLA" />
        </Group>
      </Area>
      <!-- Add more <Area> blocks for additional entity groups -->
    </SiteMap>
    <LocalizedNames><LocalizedName description="{{App Display Name}}" languagecode="1033" /></LocalizedNames>
  </AppModuleSiteMap>
</AppModuleSiteMaps>
<AppModules>
  <AppModule>
    <UniqueName>{{prefix}}_{{appname}}</UniqueName>
    <IntroducedVersion>1.0.0.0</IntroducedVersion>
    <WebResourceId>953b9fac-1e5e-e611-80d6-00155ded156f</WebResourceId>
    <OptimizedFor></OptimizedFor>
    <statecode>0</statecode><statuscode>1</statuscode>
    <FormFactor>1</FormFactor>
    <ClientType>4</ClientType>
    <NavigationType>0</NavigationType>
    <AppModuleComponents>
      <!-- type="1" for each entity, type="62" for the SiteMap itself -->
      <AppModuleComponent type="1" schemaName="{{prefix}}_{{entity}}" />
      <AppModuleComponent type="62" schemaName="{{prefix}}_{{appname}}" />
    </AppModuleComponents>
    <AppModuleRoleMaps />
    <LocalizedNames><LocalizedName description="{{App Display Name}}" languagecode="1033" /></LocalizedNames>
    <Descriptions><Description description="{{Description}}" languagecode="1033" /></Descriptions>
    <appsettings>
      <appsetting settingdefinitionid.uniquename="AppChannel">
        <iscustomizable>1</iscustomizable>
        <value>1</value>
      </appsetting>
    </appsettings>
  </AppModule>
</AppModules>
```

---

## pack.sh

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOLUTION_DIR="$SCRIPT_DIR/{{SolutionName}}"
OUTPUT="$SCRIPT_DIR/{{SolutionName}}.zip"
echo "Packing from: $SOLUTION_DIR"
cd "$SOLUTION_DIR"
zip -j "$OUTPUT" "[Content_Types].xml" solution.xml customizations.xml
echo "Created: $OUTPUT"
echo ""
echo "Import:  pac solution import --path $OUTPUT"
echo "Browser: make.powerapps.com → Solutions → Import Solution"
```

Files must sit at the **zip root** — `-j` (junk paths) is required.

---

## Critical Gotchas (verified from real import testing)

1. **solution.xml root element** must include `OrganizationVersion`, `OrganizationSchemaType`, `CRMServerServiceabilityVersion`, and `SolutionPackageVersion="9.2"`. Copy the exact attribute set from these projects.

2. **Primary name field** = `PrimaryName` flag in `<DisplayMask>`. No separate element or attribute needed.

3. **No system attributes** — do not declare `statecode`, `statuscode`, `createdon`, `modifiedon`, `ownerid`, etc. Dataverse creates them automatically. Declaring them causes a duplicate key import error.

4. **`<attributes>` before entity properties** — `<attributes>` must be the first child of `<entity>`. Entity-level properties (`<EntitySetName>`, `<OwnershipTypeMask>`, etc.) come after the closing `</attributes>`.

5. **Attribute display labels** = `<displaynames>/<displayname>` (lowercase). NOT `<LocalizedNames>/<LocalizedName>`.

6. **Option value labels** = lowercase `<labels>/<label>`. NOT `<Labels>/<Label>`.

7. **Multiline text** = `<Type>nvarchar</Type>` + `<Format>textarea</Format>`. `<Type>memo</Type>` is not recognised and causes import failure.

8. **View GUIDs must be fresh** on every import attempt. Failed-import GUIDs are persisted in the environment; re-using them causes the view import to be silently skipped or fail.

9. **`<returnedtypecode>`** = entity logical name string (e.g., `{{prefix}}_todo`), not a numeric code.

10. **ImeMode** = string: `auto`, `inactive`, or `disabled`. Not an integer.

11. **Simple boolean properties** — use `<IsCustomizable>1</IsCustomizable>`, NOT `<IsCustomizable><Value>1</Value><CanModify>1</CanModify></IsCustomizable>`. The compound form triggers "string '11' is not a valid Boolean value" on import.

12. **Boolean (Two Options) uses two different type values** — `<Type>bit</Type>` (physical storage, on the attribute) and `<OptionSetType>bool</OptionSetType>` (option set category, inside `<optionset>`). These are NOT interchangeable. Using `bool` for `<Type>` causes "Unable to find attribute type by name bool" on import; using `bit` for `<OptionSetType>` causes the field to render as non-editable in the form.

13. **Boolean fields require `<DefaultValue>`** — without `<DefaultValue>0</DefaultValue>` (or `1`) the field renders as read-only / non-interactive in the model-driven form. Always include it immediately before the `<optionset>` element.
