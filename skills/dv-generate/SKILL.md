---
name: dv-generate
description: Generate source-controlled, unmanaged Dataverse solution XML files (customizations.xml, solution.xml, pack.sh) without a live environment. Use when the user wants to create a new solution from scratch, add tables/fields/views/forms, or scaffold a model-driven app with AppModule and SiteMap. Adds and changes components by regenerating, does not remove them, and pulls manual dev changes back into the saved XML. Also use when the user asks what changed in the dev environment, wants to sync or pull the saved XML with dev, or says they made changes by hand in dev. Always ask for the publisher prefix before generating any XML.
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

## Solutions are always unmanaged

**dv-generate only produces unmanaged solutions (`<Managed>0</Managed>`). There is no managed option.** If the user asks for a managed solution, explain the deployment flow below instead of setting `<Managed>1</Managed>`.

Unmanaged solutions can be re-imported as simple overwrites, so iterating in a development environment does not trigger the staged upgrade (`ImportAsHolding`) and statecode deletion errors that hand-written managed solutions hit. Microsoft's guidance on hand-editing the customizations file also covers unmanaged exports only.

### Deploying: export as managed from dev

When you want to deploy beyond development:

1. Import the generated unmanaged solution into a **dev** environment (`pac solution import --path MySolution.zip`, or make.powerapps.com → Solutions → Import solution).
2. From dev, **export it as managed** (make.powerapps.com → Solutions → Export → Managed, or `pac solution export --name {{SolutionUniqueName}} --path out --managed`).
3. Deploy the exported managed zip to test, UAT and production.

The platform writes the managed package itself, so layering, upgrade and delete behaviour are correct. Do not edit `<Managed>` by hand to produce one.

### Publisher block

The publisher block in `solution.xml` needs:
- `<UniqueName>` — a PascalCase identifier for the publisher (e.g., `ContosoInc`)
- `<CustomizationPrefix>` — the lowercase prefix (e.g., `contoso`)
- `<CustomizationOptionValuePrefix>` — a unique integer (e.g., `10000`); must not clash with other publishers in the same environment

---

## Changing a solution after its first release

Results below come from the 16-scenario regeneration matrix in `tests/regen/` (unmanaged dev environment plus a separate managed target). Anything not listed was not tested.

### What regenerating does reliably

Edit the saved XML in place, bump `<Version>`, import into dev with `pac solution import --path X.zip --environment <dev> --publish-changes` (an overwrite), test, then export as managed and import into the sandbox as an **upgrade** (`pac solution import --path X.zip --stage-and-upgrade`). This worked on every path for:

- adding a column, a picklist option, a table, an environment variable or a connection reference
- changing a column label or an environment variable default

### Out of scope: removing components and changing a column's type

dv-generate does not remove anything and does not change a column's type. Leaving a component out of the saved XML does not remove it from dev, and dropping it from the XML would leave the XML and dev out of step. Do not do it quietly. When the user asks for a removal or a type change, say it is out of scope, leave that component in the XML, and tell them to make the change in the maker portal in dev and then bring it back with `pull.py` (below).

What the tests showed, so you can warn the user:

- The solution includes everything that exists on a table (`RootComponent behavior="0"`), so a column, view, form or choice option left out of the XML stays in dev and in the managed export.
- Dataverse refuses to delete a column while a form or view uses it ("Object dependencies exist"). After one portal import of a zip that no longer used the column, dev's form and Quick Find view still did.
- Removing a table, environment variable, connection reference or app by deleting the solution wrapper and re-importing worked in testing, but a managed upgrade then deletes the table and **all its rows** in the target, and it fails if an app still references the table.
- A plain update (not `--stage-and-upgrade`) removes nothing in the target.
- Changing a column's type is rejected on import.
- Importing a release that removes a choice option hung on 2 of 4 attempts.

### Rules when regenerating

1. **Pull first** (below), so manual edits made in dev are not overwritten. An overwrite import replaces any view or form that shares a GUID with the saved XML.
2. Edit the saved files in place. Never change a schema name or an existing GUID. Derive GUIDs from stable names (for example `uuid5` of the prefix, table and component name) so regenerating the same spec gives the same GUIDs.
3. Import into dev with `pac solution import --publish-changes`, bump the version in dev if needed (`pac solution online-version --solution-name X --solution-version 1.0.0.N --environment <dev>`), and export as managed.
4. Import the same managed zip into the sandbox, then production.

### Bringing manual changes back from dev

Use this when the user asks what changed in dev, wants the saved XML brought in line with dev, or says they edited the solution by hand in dev. Requests look like: "what has changed in dev since I last saved TodoSolution?" or "bring my manual changes in dev back into the saved XML". You need the dev URL (`pac env list`, with `pac` already authenticated), the solution's unique name (`pac solution list --environment <dev-url>`) and the folder holding the saved `solution.xml`. Run `scripts/pull.py` yourself and show the user the report. Describe what exists on each side; do not guess who changed what or when (a column in dev that is missing from the saved XML may have been dropped from the XML, not added in dev). To fold a change into the saved XML in the templates' style, add `--keep <folder>` so dev's extracted export is left in that folder, then read the component's definition from its `customizations.xml`. Use `--apply` only if the user asks for dev's export to replace the saved XML.

`scripts/pull.py --env <dev-url> --solution <UniqueName> --dir <SolutionDir>` exports the **unmanaged** solution from dev and reports what differs from the saved XML, in both directions: in dev but not in the saved XML, in the saved XML but not in dev, and different between the two. It compares tables, custom columns and their types, labels and options, views (name and columns), forms (fields), environment variables, connection references and app tables. Platform system columns and system views are ignored. It changes nothing unless you add `--apply`.

- **Fold the changes in by hand:** use the report to edit the saved XML in the templates' style. The report names the components but does not generate the XML.
- **Adopt dev wholesale:** `--apply` replaces `solution.xml`, `customizations.xml`, `[Content_Types].xml` and `environmentvariabledefinitions/` with dev's export. Review with `git diff`; commit first so you can undo. The export is the platform's XML, not the skill's templates (it includes system columns, for example), so later edits work on that XML and the template checks no longer apply. In testing, an adopted export re-imported cleanly and a second pull showed no drift.
- **A removal made in dev** appears as "in the saved XML, not in dev". Remove it from the saved XML, or use `--apply`.

Not compared: charts, dashboards, business rules, relationships, security roles, form scripts, and the site map beyond which tables an app lists. It cannot read a managed solution, so it only works against the unmanaged copy in dev.

---

## Skill boundaries

| Need | Use instead |
|---|---|
| Produce a managed package | Import the unmanaged zip into dev, then export as managed (see "Deploying: export as managed from dev") |
| Export/import/pack/unpack via PAC CLI | **dv-solution** |
| Query or read Dataverse records | **dv-query** |
| Create/update records via API | **dv-data** |
| Connect to Dataverse / configure auth | **dv-connect** |

---

## File Structure

Every importable solution zip contains **three files at the zip root**, plus an `environmentvariabledefinitions/` folder if the solution has environment variables:

```
[Content_Types].xml
solution.xml
customizations.xml
environmentvariabledefinitions/        (only if environment variables are used)
  {{prefix}}_{{VariableName}}/environmentvariabledefinition.xml
```

Pack with:
```bash
cd MySolutionDir
zip -r ../MySolution.zip "[Content_Types].xml" solution.xml customizations.xml environmentvariabledefinitions
```
(Omit `environmentvariabledefinitions` if the folder does not exist.)

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

Verified from a working Dataverse export. Three things differ from other attribute types:

1. `<AppDefaultValue>0</AppDefaultValue>` — NOT `<DefaultValue>` (wrong element, causes read-only rendering)
2. Optionset name is **entity-qualified**: `{{prefix}}_{{entity}}_{{fieldname}}` — not just `{{prefix}}_{{fieldname}}`
3. `<OptionSetType>bit</OptionSetType>` — NOT `bool`
4. Options use `<option value="1">` / `<option value="0">` — NOT `<TrueOption>` / `<FalseOption>`
5. Form control classid `{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}` is correct — but **must include `disabled="false"`** or the control renders read-only

```xml
<attribute PhysicalName="{{prefix}}_{{FieldnameCapitalised}}">
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
  <IsSearchable>0</IsSearchable><IsFilterable>0</IsFilterable><IsRetrievable>0</IsRetrievable><IsLocalizable>0</IsLocalizable>
  <AppDefaultValue>0</AppDefaultValue>
  <optionset Name="{{prefix}}_{{entity}}_{{fieldname}}">
    <OptionSetType>bit</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>
    <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
    <Descriptions><Description description="" languagecode="1033" /></Descriptions>
    <options>
      <option value="1" ExternalValue="" IsHidden="0"><labels><label description="Yes" languagecode="1033" /></labels></option>
      <option value="0" ExternalValue="" IsHidden="0"><labels><label description="No" languagecode="1033" /></labels></option>
    </options>
  </optionset>
  <displaynames><displayname description="{{Field Label}}" languagecode="1033" /></displaynames>
  <Descriptions><Description description="" languagecode="1033" /></Descriptions>
</attribute>
```

Form control:
```xml
<control id="{{prefix}}_{{fieldname}}" classid="{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}" datafieldname="{{prefix}}_{{fieldname}}" disabled="false" />
```

---

## View Templates

Every entity needs at minimum: a list view (`querytype 0`) and a Quick Find view (`querytype 4`). Dataverse also creates its own system views (Active, Inactive, Advanced Find, Associated, Lookup), so custom views appear alongside them.

**Structure (verified by import and re-export):**
- `<savedquery>` elements must be wrapped in a `<savedqueries>` element inside `<SavedQueries>`. **Without the wrapper the import still reports success but silently drops every view**, and `pac solution unpack` fails with `Value cannot be null. (Parameter 'other')`.
- Do **not** include `<columnsetxml>`. Importing it fails with "The FetchXml (<columnset>…) is invalid".
- The view's columns come from `<layoutxml>` and `<fetchxml>`. `<returnedtypecode>` is not needed (real exports omit it); if you do include it, use the entity logical name string, not a number.
- A Quick Find view needs `<filter type="or" isquickfindfields="1">` with a `like` condition on each searchable column, using the value `{0}`.

**GUIDs must be stable.** Generate each `savedqueryid` once, commit it, and never regenerate it. Re-importing with the same GUID updates the view in place; a new GUID creates a duplicate view. Generate with:
```bash
python3 -c "import uuid; print('{' + str(uuid.uuid4()).upper() + '}')"
```

```xml
<SavedQueries>
  <savedqueries>
    <!-- List view -->
    <savedquery>
      <IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>
      <isquickfindquery>0</isquickfindquery><isprivate>0</isprivate><isdefault>1</isdefault>
      <savedqueryid>{UNIQUE-GUID-1}</savedqueryid>
      <layoutxml><grid name="resultset" jump="{{prefix}}_{{primaryfield}}" select="1" icon="1" preview="1">
        <row name="result" id="{{prefix}}_{{entity}}id">
          <cell name="{{prefix}}_{{field1}}" width="200"/>
          <cell name="{{prefix}}_{{field2}}" width="150"/>
        </row>
      </grid></layoutxml>
      <querytype>0</querytype>
      <fetchxml><fetch version="1.0" mapping="logical">
        <entity name="{{prefix}}_{{entity}}">
          <attribute name="{{prefix}}_{{entity}}id"/>
          <attribute name="{{prefix}}_{{field1}}"/>
          <attribute name="{{prefix}}_{{field2}}"/>
          <order attribute="{{prefix}}_{{primaryfield}}" descending="false"/>
          <filter type="and"><condition attribute="statecode" operator="eq" value="0"/></filter>
        </entity>
      </fetch></fetchxml>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <LocalizedNames><LocalizedName description="All {{Plural Name}}" languagecode="1033"/></LocalizedNames>
    </savedquery>

    <!-- Quick Find view -->
    <savedquery>
      <IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>
      <isquickfindquery>1</isquickfindquery><isprivate>0</isprivate><isdefault>1</isdefault>
      <savedqueryid>{UNIQUE-GUID-2}</savedqueryid>
      <layoutxml><grid name="resultset" jump="{{prefix}}_{{primaryfield}}" select="1" icon="1" preview="1">
        <row name="result" id="{{prefix}}_{{entity}}id">
          <cell name="{{prefix}}_{{field1}}" width="200"/>
          <cell name="{{prefix}}_{{field2}}" width="150"/>
        </row>
      </grid></layoutxml>
      <querytype>4</querytype>
      <fetchxml><fetch version="1.0" mapping="logical">
        <entity name="{{prefix}}_{{entity}}">
          <attribute name="{{prefix}}_{{entity}}id"/>
          <attribute name="{{prefix}}_{{field1}}"/>
          <attribute name="{{prefix}}_{{field2}}"/>
          <order attribute="{{prefix}}_{{primaryfield}}" descending="false"/>
          <filter type="and"><condition attribute="statecode" operator="eq" value="0"/></filter>
          <filter type="or" isquickfindfields="1">
            <condition attribute="{{prefix}}_{{field1}}" operator="like" value="{0}"/>
            <condition attribute="{{prefix}}_{{field2}}" operator="like" value="{0}"/>
          </filter>
        </entity>
      </fetch></fetchxml>
      <IntroducedVersion>1.0.0.0</IntroducedVersion>
      <LocalizedNames><LocalizedName description="Quick Find {{Plural Name}}" languagecode="1033"/></LocalizedNames>
    </savedquery>
  </savedqueries>
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
| Boolean | `{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}` — **must also set `disabled="false"`** on the control element or it renders read-only |
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

## Environment Variables

Verified from a real Dataverse export. Environment variable definitions are **not** in customizations.xml. Each one is its own file at `environmentvariabledefinitions/{{prefix}}_{{VariableName}}/environmentvariabledefinition.xml` (folder name = schema name).

```xml
<environmentvariabledefinition schemaname="{{prefix}}_{{VariableName}}">
  <defaultvalue>{{default}}</defaultvalue>   <!-- omit for Secret -->
  <description default="{{Description}}">
    <label description="{{Description}}" languagecode="1033" />
  </description>
  <displayname default="{{Display Name}}">
    <label description="{{Display Name}}" languagecode="1033" />
  </displayname>
  <introducedversion>1.0.0.0</introducedversion>
  <iscustomizable>1</iscustomizable>
  <isrequired>0</isrequired>
  <secretstore>0</secretstore>
  <type>{{TypeCode}}</type>
</environmentvariabledefinition>
```

| Type | `<type>` | Example `<defaultvalue>` |
|---|---|---|
| Text | `100000000` | `Text` |
| Decimal number | `100000001` | `12` |
| Boolean (Yes/No) | `100000002` | `yes` (string, not `1`/`true`) |
| JSON | `100000003` | `{ "name":"John" }` |
| Secret | `100000005` | none — omit `<defaultvalue>` |

Data source is probably `100000004`, but that has not been verified from an export. Per-environment values (`environmentvariablevalue`) are not generated; supply them at import time with a deployment settings file (`pac solution create-settings`, then `pac solution import --settings-file`).

---

## Connection References

Verified from a real Dataverse export. Connection references go in customizations.xml between `<EntityDataProviders />` and `<Languages>`. A reference is only a pointer to a connector; the connection itself is supplied at import time (maker prompt or deployment settings file). dv-generate cannot create the flows or canvas apps that use a reference.

```xml
<connectionreferences>
  <connectionreference connectionreferencelogicalname="{{prefix}}_{{ReferenceName}}">
    <connectionreferencedisplayname>{{Display Name}}</connectionreferencedisplayname>
    <connectorid>/providers/Microsoft.PowerApps/apis/{{connector_api_name}}</connectorid>
    <description>{{Description}}</description>
    <iscustomizable>1</iscustomizable>
    <promptingbehavior>0</promptingbehavior>
    <statecode>0</statecode>
    <statuscode>1</statuscode>
  </connectionreference>
</connectionreferences>
```

Example `connectorid`: `/providers/Microsoft.PowerApps/apis/shared_azureblob`. Other shared connectors follow the same `shared_{{name}}` pattern.

**RootComponents:** do not add RootComponent entries for environment variables or connection references. The reference export left `<RootComponents />` empty even though it contained both. An import test (unmanaged, platform `9.2.26092.158`) confirmed that a solution without those entries imports cleanly and re-exports with the environment variables and connection reference intact, and that adding them (`type="380"`, `type="10066"`) made no difference to the export.

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
rm -f "$OUTPUT"
FILES=("[Content_Types].xml" solution.xml customizations.xml)
[ -d environmentvariabledefinitions ] && FILES+=(environmentvariabledefinitions)
zip -r "$OUTPUT" "${FILES[@]}"
echo "Created: $OUTPUT"
echo ""
echo "Import:  pac solution import --path $OUTPUT"
echo "Browser: make.powerapps.com → Solutions → Import Solution"
```

`[Content_Types].xml`, solution.xml and customizations.xml must sit at the **zip root**. Do not use `zip -j`, which would flatten the `environmentvariabledefinitions/` folder.

---

## Critical Gotchas (verified from real import testing)

1. **solution.xml root element** must include `OrganizationVersion`, `OrganizationSchemaType`, `CRMServerServiceabilityVersion`, and `SolutionPackageVersion="9.2"`. Copy the exact attribute set from these projects.

2. **Primary name field** = `PrimaryName` flag in `<DisplayMask>`. No separate element or attribute needed.

3. **No system attributes** — do not declare `statecode`, `statuscode`, `createdon`, `modifiedon`, `ownerid`, etc. Dataverse creates them automatically. Declaring them causes a duplicate key import error.

4. **`<attributes>` before entity properties** — `<attributes>` must be the first child of `<entity>`. Entity-level properties (`<EntitySetName>`, `<OwnershipTypeMask>`, etc.) come after the closing `</attributes>`.

5. **Attribute display labels** = `<displaynames>/<displayname>` (lowercase). NOT `<LocalizedNames>/<LocalizedName>`.

6. **Option value labels** = lowercase `<labels>/<label>`. NOT `<Labels>/<Label>`.

7. **Multiline text** = `<Type>nvarchar</Type>` + `<Format>textarea</Format>`. `<Type>memo</Type>` is not recognised and causes import failure.

8. **View GUIDs must be stable, and views need the `<savedqueries>` wrapper.** A new GUID on re-import creates a duplicate view; the same GUID updates it. Earlier advice to regenerate GUIDs per attempt was wrong — views were being silently dropped because the `<savedqueries>` wrapper was missing (see View Templates).

9. **`<returnedtypecode>`** is optional on views. If present it is the entity logical name string (e.g., `{{prefix}}_todo`), not a numeric code.

10. **ImeMode** = string: `auto`, `inactive`, or `disabled`. Not an integer.

11. **Simple boolean properties** — use `<IsCustomizable>1</IsCustomizable>`, NOT `<IsCustomizable><Value>1</Value><CanModify>1</CanModify></IsCustomizable>`. The compound form triggers "string '11' is not a valid Boolean value" on import.

12. **Boolean (Two Options) — verified correct structure** (reverse-engineered from working export):
    - `<Type>bit</Type>` on the attribute
    - `<AppDefaultValue>0</AppDefaultValue>` — NOT `<DefaultValue>` (wrong element name, causes read-only)
    - Optionset name must be entity-qualified: `{{prefix}}_{{entity}}_{{fieldname}}`
    - `<OptionSetType>bit</OptionSetType>` inside the optionset — NOT `bool`
    - Options use `<option value="1">` / `<option value="0">` — NOT `<TrueOption>` / `<FalseOption>`
    - Form control classid `{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}` is correct — but **`disabled="false"` is required** on the control or it renders read-only

13. **Generate unmanaged only; re-import as an overwrite** — hand-written managed solutions trigger "ImportAsHolding" (staged upgrade) on re-import, which diffs entity attributes and tries to delete system fields (`statecode`, `statuscode`), causing an unresolvable import failure. Unmanaged re-imports are simple overwrites. To get a managed package, import to dev and export as managed (see "Deploying: export as managed from dev").

14. **`<RootComponent behavior="0">` is correct for entity components** — Microsoft defines the values as `0` = Include Subcomponents, `1` = Do not include subcomponents, `2` = Include As Shell Only. Use `behavior="0"` as shown in all Microsoft solution exports. Because `0` includes every subcomponent that exists on the table in the environment, deleting a column or view from the generated XML does **not** remove it from the solution or from a managed export; it must be deleted in the dev environment too.

15. **Holding solutions from failed managed imports block re-import** — if an earlier managed upgrade attempt left a residual `_Upgrade` holding solution in the environment, check `make.powerapps.com → Solutions` for any solution with `_Upgrade` or `(patch)` in the name and delete it alongside the main solution before re-importing.
