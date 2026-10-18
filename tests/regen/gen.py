"""Parameterised solution generator for the regeneration tests.

build(spec, outdir) writes solution.xml, customizations.xml, [Content_Types].xml and
environmentvariabledefinitions/ for a spec, using the templates in skills/dv-generate/SKILL.md.
All GUIDs are derived from stable names (uuid5) so regenerating an unchanged part of a spec gives
identical GUIDs, which is what makes re-import an in-place overwrite instead of a duplicate.

spec = {
  "code": "aa",                      # scenario code, letters only; prefix is 'dvg' + code
  "version": "1.0.0.0",
  "entities": [ {"name": "alpha", "display": "Alpha",
                 "cols": [("text","name","Name"), ("decimal","amount","Amount"),
                          ("int","count","Count"), ("picklist","status","Status",["a","b"]),
                          ("bool","flag","Flag")],
                 "views": ["all", "qf"] } ],
  "app": True,                       # AppModule + SiteMap listing every entity
  "envvars": [("ev1", 100000000, "x")],
  "connrefs": ["cr1"],
}
The first column of every entity must be the primary name text column.
"""
import os
import uuid
from xml.sax.saxutils import escape

NS = uuid.NAMESPACE_URL

COMMON = (
    "<IsCustomField>1</IsCustomField><IsAuditEnabled>1</IsAuditEnabled><IsSecured>0</IsSecured>\n"
    "  <IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><IsRenameable>1</IsRenameable>\n"
    "  <CanModifySearchSettings>1</CanModifySearchSettings><CanModifyRequirementLevelSettings>1</CanModifyRequirementLevelSettings>\n"
    "  <CanModifyAdditionalSettings>1</CanModifyAdditionalSettings><SourceType>0</SourceType>\n"
    "  <IsGlobalFilterEnabled>0</IsGlobalFilterEnabled><IsSortableEnabled>0</IsSortableEnabled>\n"
    "  <CanModifyGlobalFilterSettings>1</CanModifyGlobalFilterSettings><CanModifyIsSortableSettings>1</CanModifyIsSortableSettings>\n"
    "  <IsDataSourceSecret>0</IsDataSourceSecret><AutoNumberFormat></AutoNumberFormat>\n"
)
API = "<ValidForUpdateApi>1</ValidForUpdateApi><ValidForReadApi>1</ValidForReadApi><ValidForCreateApi>1</ValidForCreateApi>"
LABEL = '<displaynames><displayname description="{l}" languagecode="1033" /></displaynames>\n  <Descriptions><Description description="" languagecode="1033" /></Descriptions>'

ENTITY_PROPS = (
    "<IsDuplicateCheckSupported>1</IsDuplicateCheckSupported><IsBusinessProcessEnabled>0</IsBusinessProcessEnabled><IsRequiredOffline>0</IsRequiredOffline>"
    "<IsInteractionCentricEnabled>0</IsInteractionCentricEnabled><IsCollaboration>0</IsCollaboration><AutoRouteToOwnerQueue>0</AutoRouteToOwnerQueue>"
    "<IsConnectionsEnabled>0</IsConnectionsEnabled><EntityColor></EntityColor><IsDocumentManagementEnabled>0</IsDocumentManagementEnabled>"
    "<AutoCreateAccessTeams>0</AutoCreateAccessTeams><IsOneNoteIntegrationEnabled>0</IsOneNoteIntegrationEnabled><IsKnowledgeManagementEnabled>0</IsKnowledgeManagementEnabled>"
    "<IsSLAEnabled>0</IsSLAEnabled><IsDocumentRecommendationsEnabled>0</IsDocumentRecommendationsEnabled><IsBPFEntity>0</IsBPFEntity>"
    "<OwnershipTypeMask>UserOwned</OwnershipTypeMask><IsAuditEnabled>0</IsAuditEnabled><IsRetrieveAuditEnabled>0</IsRetrieveAuditEnabled>"
    "<IsRetrieveMultipleAuditEnabled>0</IsRetrieveMultipleAuditEnabled><IsActivity>0</IsActivity><ActivityTypeMask></ActivityTypeMask><IsActivityParty>0</IsActivityParty>"
    "<IsReplicated>0</IsReplicated><IsReplicationUserFiltered>0</IsReplicationUserFiltered><IsMailMergeEnabled>1</IsMailMergeEnabled><IsVisibleInMobile>0</IsVisibleInMobile>"
    "<IsVisibleInMobileClient>0</IsVisibleInMobileClient><IsReadOnlyInMobileClient>0</IsReadOnlyInMobileClient><IsOfflineInMobileClient>1</IsOfflineInMobileClient>"
    "<DaysSinceRecordLastModified>0</DaysSinceRecordLastModified><MobileOfflineFilters></MobileOfflineFilters><IsMapiGridEnabled>1</IsMapiGridEnabled>"
    "<IsReadingPaneEnabled>1</IsReadingPaneEnabled><IsQuickCreateEnabled>0</IsQuickCreateEnabled><SyncToExternalSearchIndex>0</SyncToExternalSearchIndex>"
    "<IntroducedVersion>1.0</IntroducedVersion><IsCustomizable>1</IsCustomizable><IsRenameable>1</IsRenameable><IsMappable>1</IsMappable>"
    "<CanModifyAuditSettings>1</CanModifyAuditSettings><CanModifyMobileVisibility>1</CanModifyMobileVisibility><CanModifyMobileClientVisibility>1</CanModifyMobileClientVisibility>"
    "<CanModifyMobileClientReadOnly>1</CanModifyMobileClientReadOnly><CanModifyMobileClientOffline>1</CanModifyMobileClientOffline><CanModifyConnectionSettings>1</CanModifyConnectionSettings>"
    "<CanModifyDuplicateDetectionSettings>1</CanModifyDuplicateDetectionSettings><CanModifyMailMergeSettings>1</CanModifyMailMergeSettings><CanModifyQueueSettings>1</CanModifyQueueSettings>"
    "<CanCreateAttributes>1</CanCreateAttributes><CanCreateForms>1</CanCreateForms><CanCreateCharts>1</CanCreateCharts><CanCreateViews>1</CanCreateViews>"
    "<CanModifyAdditionalSettings>1</CanModifyAdditionalSettings><CanEnableSyncToExternalSearchIndex>1</CanEnableSyncToExternalSearchIndex><EnforceStateTransitions>0</EnforceStateTransitions>"
    "<CanChangeHierarchicalRelationship>1</CanChangeHierarchicalRelationship><EntityHelpUrlEnabled>0</EntityHelpUrlEnabled><ChangeTrackingEnabled>1</ChangeTrackingEnabled>"
    "<CanChangeTrackingBeEnabled>1</CanChangeTrackingBeEnabled><IsEnabledForExternalChannels>0</IsEnabledForExternalChannels><IsMSTeamsIntegrationEnabled>0</IsMSTeamsIntegrationEnabled>"
    "<IsSolutionAware>0</IsSolutionAware>"
)

CLASSID = {
    "text": "{4273EDBD-AC1D-40d3-9FB2-095C621B552D}",
    "picklist": "{3EF39988-22BB-4f0b-BBBE-64B5A3748AEE}",
    "decimal": "{C3EFE0C3-0EC6-42be-8349-CBD9079C717A}",
    "int": "{C3EFE0C3-0EC6-42be-8349-CBD9079C717A}",
    "bool": "{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}",
}


def prefix(spec):
    return "dvg" + spec["code"]


def solution_name(spec):
    return "DvgRegen" + spec["code"].capitalize()


def build(spec, out):
    pfx = prefix(spec)

    def guid(*key):
        return "{" + str(uuid.uuid5(NS, "-".join((pfx,) + key))).upper() + "}"

    def write(path, text):
        p = os.path.join(out, path)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)

    def attribute(name, typ, label, tail, ime="auto", flags=(0, 0, 0, 0), primary=False, physical=None):
        mask = ("PrimaryName|ValidForAdvancedFind|ValidForForm|ValidForGrid|RequiredForForm" if primary
                else "ValidForAdvancedFind|ValidForForm|ValidForGrid")
        s, f, r, loc = flags
        return (
            f'<attribute PhysicalName="{physical or name}">\n'
            f"  <Type>{typ}</Type><Name>{name}</Name><LogicalName>{name}</LogicalName>\n"
            f"  <RequiredLevel>none</RequiredLevel>\n  <DisplayMask>{mask}</DisplayMask>\n  <ImeMode>{ime}</ImeMode>\n"
            f"  {API}\n  {COMMON}"
            f"  <IsSearchable>{s}</IsSearchable><IsFilterable>{f}</IsFilterable><IsRetrievable>{r}</IsRetrievable><IsLocalizable>{loc}</IsLocalizable>\n"
            f"  {tail}\n  {LABEL.format(l=escape(label))}\n</attribute>"
        )

    def options(items, base=100000000):
        return "".join(
            f'<option value="{base + i}"><labels><label description="{t}" languagecode="1033" /></labels>'
            f'<Descriptions><Description description="" languagecode="1033" /></Descriptions></option>'
            for i, t in enumerate(items))

    def column(ent, col):
        kind, short, label = col[0], col[1], col[2]
        name = f"{pfx}_{short}"
        if kind == "text":
            primary = col is ent["cols"][0]
            return attribute(name, "nvarchar", label, "<Format>text</Format><MaxLength>100</MaxLength><Length>200</Length>", primary=primary)
        if kind == "decimal":
            return attribute(name, "decimal", label, "<Precision>2</Precision><MinValue>0</MinValue><MaxValue>100000000000</MaxValue>", ime="inactive", flags=(0, 1, 1, 0))
        if kind == "int":
            return attribute(name, "int", label, "<MinValue>-2147483648</MinValue><MaxValue>2147483647</MaxValue>", ime="inactive", flags=(0, 1, 1, 0))
        if kind == "picklist":
            opt = (f'<optionset Name="{name}">\n    <OptionSetType>picklist</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>\n'
                   f"    {LABEL.format(l=escape(label))}\n    <options>{options(col[3])}</options>\n  </optionset>")
            return attribute(name, "picklist", label, opt, flags=(0, 1, 1, 0))
        if kind == "bool":
            opt = (f'<AppDefaultValue>0</AppDefaultValue>\n  <optionset Name="{pfx}_{ent["name"]}_{short}">\n'
                   f"    <OptionSetType>bit</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>\n"
                   f"    {LABEL.format(l=escape(label))}\n    <options>\n"
                   f'      <option value="1" ExternalValue="" IsHidden="0"><labels><label description="Yes" languagecode="1033" /></labels></option>\n'
                   f'      <option value="0" ExternalValue="" IsHidden="0"><labels><label description="No" languagecode="1033" /></labels></option>\n'
                   f"    </options>\n  </optionset>")
            return attribute(name, "bit", label, opt, physical=f"{pfx}_{short.capitalize()}")
        raise ValueError(kind)

    def plural(ent):
        return f"{ent['display']}s {spec['code']}"

    def view(ent, kind):
        qtype, qf = (0, 0) if kind == "all" else (4, 1)
        name = ("All " if kind == "all" else "Quick Find ") + plural(ent)
        fields = [f"{pfx}_{c[1]}" for c in ent["cols"][:4]]
        primary = fields[0]
        eid = f"{pfx}_{ent['name']}id"
        cells = "".join(f'<cell name="{f}" width="150"/>' for f in fields)
        attrs = "".join(f'<attribute name="{f}"/>' for f in fields)
        qfx = ""
        if qf:
            qfx = '<filter type="or" isquickfindfields="1">' + "".join(
                f'<condition attribute="{f}" operator="like" value="{{0}}"/>' for f in fields[:2]) + "</filter>"
        return (
            f"<savedquery><IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted><isquickfindquery>{qf}</isquickfindquery>"
            f"<isprivate>0</isprivate><isdefault>1</isdefault><savedqueryid>{guid(ent['name'], 'view', kind)}</savedqueryid>"
            f'<layoutxml><grid name="resultset" jump="{primary}" select="1" icon="1" preview="1"><row name="result" id="{eid}">{cells}</row></grid></layoutxml>'
            f'<querytype>{qtype}</querytype><fetchxml><fetch version="1.0" mapping="logical"><entity name="{pfx}_{ent["name"]}"><attribute name="{eid}"/>{attrs}'
            f'<order attribute="{primary}" descending="false"/><filter type="and"><condition attribute="statecode" operator="eq" value="0"/></filter>{qfx}</entity></fetch></fetchxml>'
            f'<IntroducedVersion>1.0.0.0</IntroducedVersion><LocalizedNames><LocalizedName description="{name}" languagecode="1033"/></LocalizedNames></savedquery>'
        )

    def form(ent):
        rows = ""
        for c in ent["cols"]:
            nm = f"{pfx}_{c[1]}"
            ctl = f'<control id="{nm}" classid="{CLASSID[c[0]]}" datafieldname="{nm}"' + (' disabled="false"' if c[0] == "bool" else "") + " />"
            rows += f'<row><cell id="{guid(ent["name"], "cell", c[1])}"><labels><label description="{escape(c[2])}" languagecode="1033" /></labels>{ctl}</cell></row>'
        rows += (f'<row><cell id="{guid(ent["name"], "cell", "owner")}"><labels><label description="Owner" languagecode="1033" /></labels>'
                 f'<control id="ownerid" classid="{{270BD3DB-D9AF-4782-9025-509E298DEC0A}}" datafieldname="ownerid" /></cell></row>')
        return (
            f'<FormXml><forms type="main"><systemform><formid>{guid(ent["name"], "form")}</formid><IntroducedVersion>1.0</IntroducedVersion><FormPresentation>1</FormPresentation>'
            f'<FormActivationState>1</FormActivationState><form><tabs><tab verticallayout="true" id="{guid(ent["name"], "tab")}" IsUserDefined="1"><labels><label description="General" languagecode="1033" /></labels>'
            f'<columns><column width="100%"><sections><section showlabel="false" showbar="false" IsUserDefined="0" id="{guid(ent["name"], "section")}"><labels><label description="General" languagecode="1033" /></labels>'
            f"<rows>{rows}</rows></section></sections></column></columns></tab></tabs></form><IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>"
            f'<LocalizedNames><LocalizedName description="Information" languagecode="1033" /></LocalizedNames><Descriptions><Description description="" languagecode="1033" /></Descriptions></systemform></forms></FormXml>'
        )

    def entity(ent):
        attrs = "\n".join(column(ent, c) for c in ent["cols"])
        views = "".join(view(ent, k) for k in ent.get("views", ["all", "qf"]))
        sq = f"<SavedQueries><savedqueries>{views}</savedqueries></SavedQueries>" if views else "<SavedQueries />"
        return (
            f'<Entity>\n<Name LocalizedName="{ent["display"]}" OriginalName="{ent["display"]}">{pfx}_{ent["name"]}</Name>\n<EntityInfo><entity Name="{pfx}_{ent["name"]}">\n'
            f'<LocalizedNames><LocalizedName description="{ent["display"]}" languagecode="1033" /></LocalizedNames>\n'
            f'<LocalizedCollectionNames><LocalizedCollectionName description="{plural(ent)}" languagecode="1033" /></LocalizedCollectionNames>\n'
            f'<Descriptions><Description description="" languagecode="1033" /></Descriptions>\n<attributes>\n{attrs}\n</attributes>\n'
            f"<EntitySetName>{pfx}_{ent['name']}s</EntitySetName>\n{ENTITY_PROPS}\n</entity></EntityInfo>\n"
            '<RibbonDiffXml><CustomActions /><Templates><RibbonTemplates Id="Mscrm.Templates"></RibbonTemplates></Templates><CommandDefinitions />'
            "<RuleDefinitions><TabDisplayRules /><DisplayRules /><EnableRules /></RuleDefinitions><LocLabels /></RibbonDiffXml>\n"
            f"{form(ent)}\n{sq}\n</Entity>"
        )

    ents = spec["entities"]
    app_name = f"{pfx}_app"

    def area(e):
        n = e["name"]
        return (
            f'<Area Id="area_{pfx}_{n}" ResourceId="SitemapDesigner.NewTitle" DescriptionResourceId="SitemapDesigner.NewTitle" ShowGroups="true" IntroducedVersion="7.0.0.0">'
            f'<Titles><Title LCID="1033" Title="{e["display"]}s" /></Titles>'
            f'<Group Id="group_{pfx}_{n}" ResourceId="SitemapDesigner.NewGroup" DescriptionResourceId="SitemapDesigner.NewGroup" IntroducedVersion="7.0.0.0" IsProfile="false" ToolTipResourseId="SitemapDesigner.Unknown">'
            f'<SubArea Id="subarea_{pfx}_{n}" Icon="/_imgs/imagestrips/transparent_spacer.gif" Entity="{pfx}_{n}" Client="All,Outlook,OutlookLaptopClient,OutlookWorkstationClient,Web" AvailableOffline="true" PassParams="false" Sku="All,OnPremise,Live,SPLA" />'
            f"</Group></Area>"
        )

    app = ""
    if spec.get("app") and ents:
        comps = "".join(f'<AppModuleComponent type="1" schemaName="{pfx}_{e["name"]}" />' for e in ents)
        app = (
            f"<AppModuleSiteMaps><AppModuleSiteMap><SiteMapUniqueName>{app_name}</SiteMapUniqueName><EnableCollapsibleGroups>False</EnableCollapsibleGroups>"
            f'<ShowHome>True</ShowHome><ShowPinned>True</ShowPinned><ShowRecents>True</ShowRecents><SiteMap IntroducedVersion="7.0.0.0">{"".join(area(e) for e in ents)}</SiteMap>'
            f'<LocalizedNames><LocalizedName description="Regen {spec["code"]}" languagecode="1033" /></LocalizedNames></AppModuleSiteMap></AppModuleSiteMaps>'
            f"<AppModules><AppModule><UniqueName>{app_name}</UniqueName><IntroducedVersion>1.0.0.0</IntroducedVersion><WebResourceId>953b9fac-1e5e-e611-80d6-00155ded156f</WebResourceId>"
            f"<OptimizedFor></OptimizedFor><statecode>0</statecode><statuscode>1</statuscode><FormFactor>1</FormFactor><ClientType>4</ClientType><NavigationType>0</NavigationType>"
            f'<AppModuleComponents>{comps}<AppModuleComponent type="62" schemaName="{app_name}" /></AppModuleComponents><AppModuleRoleMaps />'
            f'<LocalizedNames><LocalizedName description="Regen {spec["code"]}" languagecode="1033" /></LocalizedNames>'
            f'<Descriptions><Description description="Regen test app" languagecode="1033" /></Descriptions>'
            f'<appsettings><appsetting settingdefinitionid.uniquename="AppChannel"><iscustomizable>1</iscustomizable><value>1</value></appsetting></appsettings></AppModule></AppModules>'
        )

    cr = ""
    if spec.get("connrefs"):
        cr = "<connectionreferences>" + "".join(
            f'<connectionreference connectionreferencelogicalname="{pfx}_{n}"><connectionreferencedisplayname>{n}</connectionreferencedisplayname>'
            f"<connectorid>/providers/Microsoft.PowerApps/apis/shared_azureblob</connectorid><description>{n}</description><iscustomizable>1</iscustomizable>"
            f"<promptingbehavior>0</promptingbehavior><statecode>0</statecode><statuscode>1</statuscode></connectionreference>"
            for n in spec["connrefs"]) + "</connectionreferences>"

    write("customizations.xml", (
        '<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" OrganizationVersion="9.2.26092.158" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.26092.00168">\n'
        f"<Entities>\n{chr(10).join(entity(e) for e in ents)}\n</Entities>\n<optionsets />\n<CustomControls />\n<EntityDataProviders />\n{cr}\n"
        f"<Languages><Language>1033</Language></Languages>\n{app}\n</ImportExportXml>\n"))

    nil1 = "".join(f'<{t} xsi:nil="true"></{t}>' for t in ["City", "County", "Country", "Fax", "FreightTermsCode", "ImportSequenceNumber", "Latitude", "Line1", "Line2", "Line3", "Longitude", "Name", "PostalCode", "PostOfficeBox", "PrimaryContactName"])
    nil2 = "".join(f'<{t} xsi:nil="true"></{t}>' for t in ["StateOrProvince", "Telephone1", "Telephone2", "Telephone3", "TimeZoneRuleVersionNumber", "UPSZone", "UTCOffset", "UTCConversionTimeZoneCode"])
    addr = lambda n: f"<Address><AddressNumber>{n}</AddressNumber><AddressTypeCode>1</AddressTypeCode>{nil1}<ShippingMethodCode>1</ShippingMethodCode>{nil2}</Address>"
    roots = "".join(f'<RootComponent type="1" schemaName="{pfx}_{e["name"]}" behavior="0" />' for e in ents)
    missing = "<MissingDependencies />"
    if app:
        roots += f'<RootComponent type="62" schemaName="{app_name}" behavior="0" /><RootComponent type="80" schemaName="{app_name}" behavior="0" />'
        missing = (
            "<MissingDependencies><MissingDependency>"
            '<Required type="61" schemaName="msdyn_/Images/AppModule_Default_Icon.png" displayName="msdyn_/Images/AppModule_Default_Icon.png" solution="AppModuleWebResources (2.5)">'
            '<package appName="AppModule Web Resources Package" version="2.5">AppModuleWebResources (2.5)</package></Required>'
            f'<Dependent type="80" schemaName="{app_name}" displayName="Regen {spec["code"]}" /></MissingDependency>'
            "<MissingDependency>"
            '<Required type="SettingDefinition" displayName="AppChannel" solution="msdyn_AppFrameworkInfraExtensions (1.0.0.16)" id.uniquename="AppChannel">'
            '<package appName="PowerAppsAppFramework Package" version="1.0.0.25">PowerAppsAppFramework_Anchor (1.0.0.25)</package></Required>'
            f'<Dependent type="AppSetting" displayName="parentappmoduleid.uniquename={app_name},settingdefinitionid.uniquename=AppChannel" id.parentappmoduleid.uniquename="{app_name}" id.settingdefinitionid.uniquename="AppChannel" />'
            "</MissingDependency></MissingDependencies>")
    uname = solution_name(spec)
    write("solution.xml", (
        '<ImportExportXml version="9.2.26092.158" SolutionPackageVersion="9.2" languagecode="1033" generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
        'OrganizationVersion="9.2.26092.158" OrganizationSchemaType="Standard" CRMServerServiceabilityVersion="9.2.26092.00168">\n'
        f"<SolutionManifest><UniqueName>{uname}</UniqueName><LocalizedNames><LocalizedName description=\"{uname}\" languagecode=\"1033\" /></LocalizedNames><Descriptions/>"
        f"<Version>{spec['version']}</Version><Managed>0</Managed><Publisher><UniqueName>DvgRegenPub{spec['code'].capitalize()}</UniqueName>"
        f"<LocalizedNames><LocalizedName description=\"Regen Pub {spec['code']}\" languagecode=\"1033\" /></LocalizedNames><Descriptions/>"
        f'<EMailAddress xsi:nil="true"></EMailAddress><SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>'
        f"<CustomizationPrefix>{pfx}</CustomizationPrefix><CustomizationOptionValuePrefix>{70000 + sum(ord(c) for c in spec['code'])}</CustomizationOptionValuePrefix>"
        f"<Addresses>{addr(1)}{addr(2)}</Addresses></Publisher><RootComponents>{roots}</RootComponents>{missing}</SolutionManifest></ImportExportXml>\n"))
    write("[Content_Types].xml", '<?xml version="1.0" encoding="utf-8"?>\n<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n  <Default Extension="xml" ContentType="application/octet-stream" />\n</Types>\n')

    for n, typ, default in spec.get("envvars", []):
        d = f"  <defaultvalue>{default}</defaultvalue>\n" if default is not None else ""
        write(f"environmentvariabledefinitions/{pfx}_{n}/environmentvariabledefinition.xml", (
            f'<environmentvariabledefinition schemaname="{pfx}_{n}">\n{d}  <description default="{n}">\n    <label description="{n}" languagecode="1033" />\n  </description>\n'
            f'  <displayname default="{n}">\n    <label description="{n}" languagecode="1033" />\n  </displayname>\n  <introducedversion>1.0.0.0</introducedversion>\n'
            f"  <iscustomizable>1</iscustomizable>\n  <isrequired>0</isrequired>\n  <secretstore>0</secretstore>\n  <type>{typ}</type>\n</environmentvariabledefinition>\n"))
