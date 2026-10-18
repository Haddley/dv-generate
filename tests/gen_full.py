#!/usr/bin/env python3
"""Generate the DvgenFull fixture by instantiating the templates in skills/dv-generate/SKILL.md.

Covers: two tables, every column type in the skill (text, multiline, decimal, integer, date,
datetime, picklist, boolean), default list + quick find views, a main form using every control
classid, an AppModule + SiteMap, and the version strings exactly as the skill documents them.

Usage: gen_full.py <output_dir>
The committed output lives in fixtures/DvgenFull/DvgenFull. Re-run this after changing SKILL.md
templates, then re-run tests/run.sh.
"""
import os
import sys
import uuid
from xml.sax.saxutils import escape

PFX = "dvgen"
OUT = sys.argv[1]

# Deterministic GUIDs so regenerated output diffs cleanly.
_n = [0]


def guid():
    _n[0] += 1
    return "{" + str(uuid.uuid5(uuid.NAMESPACE_URL, f"dvgen-full-{_n[0]}")).upper() + "}"


def write(path, text):
    p = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(text)


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


def attribute(name, typ, label, tail, ime="auto", flags=(0, 0, 0, 0), primary=False, physical=None, mid=""):
    mask = "PrimaryName|ValidForAdvancedFind|ValidForForm|ValidForGrid|RequiredForForm" if primary else "ValidForAdvancedFind|ValidForForm|ValidForGrid"
    s, f, r, loc = flags
    return (
        f'<attribute PhysicalName="{physical or name}">\n'
        f"  <Type>{typ}</Type><Name>{name}</Name><LogicalName>{name}</LogicalName>\n"
        f"  <RequiredLevel>none</RequiredLevel>\n  <DisplayMask>{mask}</DisplayMask>\n  <ImeMode>{ime}</ImeMode>\n"
        f"  {API}\n  {COMMON}"
        f"  <IsSearchable>{s}</IsSearchable><IsFilterable>{f}</IsFilterable><IsRetrievable>{r}</IsRetrievable><IsLocalizable>{loc}</IsLocalizable>\n"
        f"  {tail}{mid}\n  {LABEL.format(l=escape(label))}\n</attribute>"
    )


def options(items, base=100000000):
    out = ""
    for i, t in enumerate(items):
        out += (f'<option value="{base + i}"><labels><label description="{t}" languagecode="1033" /></labels>'
                f'<Descriptions><Description description="" languagecode="1033" /></Descriptions></option>')
    return out


def boolean_attr(entity, field, label):
    opt = (
        f'<AppDefaultValue>0</AppDefaultValue>\n  <optionset Name="{PFX}_{entity}_{field}">\n'
        f"    <OptionSetType>bit</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>\n"
        f"    {LABEL.format(l=label)}\n    <options>\n"
        f'      <option value="1" ExternalValue="" IsHidden="0"><labels><label description="Yes" languagecode="1033" /></labels></option>\n'
        f'      <option value="0" ExternalValue="" IsHidden="0"><labels><label description="No" languagecode="1033" /></labels></option>\n'
        f"    </options>\n  </optionset>"
    )
    return attribute(f"{PFX}_{field}", "bit", label, opt, flags=(0, 0, 0, 0), physical=f"{PFX}_{field.capitalize()}")


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
    "nvarchar": "{4273EDBD-AC1D-40d3-9FB2-095C621B552D}",
    "picklist": "{3EF39988-22BB-4f0b-BBBE-64B5A3748AEE}",
    "decimal": "{C3EFE0C3-0EC6-42be-8349-CBD9079C717A}",
    "int": "{C3EFE0C3-0EC6-42be-8349-CBD9079C717A}",
    "bit": "{67FAC785-CD58-4f9f-ABB3-4B7DDC6ED5ED}",
    "datetime": "{5D68B988-0661-4db2-BC3E-17598AD3BE6C}",
}


def view(entity, qtype, name, quickfind, fields, primary):
    cells = "".join(f'<cell name="{f}" width="150"/>' for f in fields)
    attrs = "".join(f'<attribute name="{f}"/>' for f in fields)
    qf = ""
    if quickfind:
        conds = "".join(f'<condition attribute="{f}" operator="like" value="{{0}}"/>' for f in fields[:2])
        qf = f'<filter type="or" isquickfindfields="1">{conds}</filter>'
    return (
        f"<savedquery><IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted><isquickfindquery>{quickfind}</isquickfindquery>"
        f"<isprivate>0</isprivate><isdefault>1</isdefault><savedqueryid>{guid()}</savedqueryid>"
        f'<layoutxml><grid name="resultset" jump="{primary}" select="1" icon="1" preview="1"><row name="result" id="{PFX}_{entity}id">{cells}</row></grid></layoutxml>'
        f'<querytype>{qtype}</querytype><fetchxml><fetch version="1.0" mapping="logical"><entity name="{PFX}_{entity}"><attribute name="{PFX}_{entity}id"/>{attrs}'
        f'<order attribute="{primary}" descending="false"/><filter type="and"><condition attribute="statecode" operator="eq" value="0"/></filter>{qf}</entity></fetch></fetchxml>'
        f'<IntroducedVersion>1.0.0.0</IntroducedVersion><LocalizedNames><LocalizedName description="{name}" languagecode="1033"/></LocalizedNames></savedquery>'
    )


def form(fields):
    rows = ""
    for name, typ, label in fields:
        ctl = f'<control id="{name}" classid="{CLASSID[typ]}" datafieldname="{name}"' + (' disabled="false"' if typ == "bit" else "") + " />"
        rows += f'<row><cell id="{guid()}"><labels><label description="{label}" languagecode="1033" /></labels>{ctl}</cell></row>'
    rows += (f'<row><cell id="{guid()}"><labels><label description="Owner" languagecode="1033" /></labels>'
             f'<control id="ownerid" classid="{{270BD3DB-D9AF-4782-9025-509E298DEC0A}}" datafieldname="ownerid" /></cell></row>')
    return (
        f'<FormXml><forms type="main"><systemform><formid>{guid()}</formid><IntroducedVersion>1.0</IntroducedVersion><FormPresentation>1</FormPresentation>'
        f'<FormActivationState>1</FormActivationState><form><tabs><tab verticallayout="true" id="{guid()}" IsUserDefined="1"><labels><label description="General" languagecode="1033" /></labels>'
        f'<columns><column width="100%"><sections><section showlabel="false" showbar="false" IsUserDefined="0" id="{guid()}"><labels><label description="General" languagecode="1033" /></labels>'
        f"<rows>{rows}</rows></section></sections></column></columns></tab></tabs></form><IsCustomizable>1</IsCustomizable><CanBeDeleted>1</CanBeDeleted>"
        f'<LocalizedNames><LocalizedName description="Information" languagecode="1033" /></LocalizedNames><Descriptions><Description description="" languagecode="1033" /></Descriptions></systemform></forms></FormXml>'
    )


def entity(name, display, plural, columns):
    """columns: list of (logical_name, type, label, attribute_xml). First is the primary name."""
    attrs = "\n".join(c[3] for c in columns)
    flds = [(c[0], c[1], c[2]) for c in columns]
    vfields = [c[0] for c in columns[:5]]
    primary = columns[0][0]
    return (
        f'<Entity>\n<Name LocalizedName="{display}" OriginalName="{display}">{PFX}_{name}</Name>\n<EntityInfo><entity Name="{PFX}_{name}">\n'
        f'<LocalizedNames><LocalizedName description="{display}" languagecode="1033" /></LocalizedNames>\n'
        f'<LocalizedCollectionNames><LocalizedCollectionName description="{plural}" languagecode="1033" /></LocalizedCollectionNames>\n'
        f'<Descriptions><Description description="" languagecode="1033" /></Descriptions>\n<attributes>\n{attrs}\n</attributes>\n'
        f"<EntitySetName>{PFX}_{name}s</EntitySetName>\n{ENTITY_PROPS}\n</entity></EntityInfo>\n"
        '<RibbonDiffXml><CustomActions /><Templates><RibbonTemplates Id="Mscrm.Templates"></RibbonTemplates></Templates><CommandDefinitions />'
        "<RuleDefinitions><TabDisplayRules /><DisplayRules /><EnableRules /></RuleDefinitions><LocLabels /></RibbonDiffXml>\n"
        f"{form(flds)}\n<SavedQueries><savedqueries>{view(name, 0, 'All ' + plural, 0, vfields, primary)}{view(name, 4, 'Quick Find ' + plural, 1, vfields, primary)}</savedqueries></SavedQueries>\n</Entity>"
    )


def text(name, label, primary=False):
    return (name, "nvarchar", label, attribute(name, "nvarchar", label, "<Format>text</Format><MaxLength>100</MaxLength><Length>200</Length>", primary=primary))


def multiline(name, label):
    return (name, "nvarchar", label, attribute(name, "nvarchar", label, "<Format>textarea</Format><MaxLength>2000</MaxLength><Length>4000</Length>"))


def decimal(name, label, minv="-100000000000"):
    return (name, "decimal", label, attribute(name, "decimal", label,
            f"<Precision>2</Precision><MinValue>{minv}</MinValue><MaxValue>100000000000</MaxValue>", ime="inactive", flags=(0, 1, 1, 0)))


def integer(name, label):
    return (name, "int", label, attribute(name, "int", label, "<MinValue>-2147483648</MinValue><MaxValue>2147483647</MaxValue>", ime="inactive", flags=(0, 1, 1, 0)))


def dt(name, label, fmt):
    return (name, "datetime", label, attribute(name, "datetime", label, f"<Format>{fmt}</Format>", ime="inactive", flags=(0, 1, 1, 0)))


def pick(name, label, items):
    opt = (f'<optionset Name="{name}">\n    <OptionSetType>picklist</OptionSetType><IsGlobal>0</IsGlobal><IsCustomizable>1</IsCustomizable>\n'
           f"    {LABEL.format(l=label)}\n    <options>{options(items)}</options>\n  </optionset>")
    return (name, "picklist", label, attribute(name, "picklist", label, opt, flags=(0, 1, 1, 0)))


def boolean(ent, field, label):
    return (f"{PFX}_{field}", "bit", label, boolean_attr(ent, field, label))


project = entity("project", "Project", "Projects", [
    text(f"{PFX}_name", "Name", primary=True),
    multiline(f"{PFX}_description", "Description"),
    decimal(f"{PFX}_budget", "Budget", minv="0"),
    integer(f"{PFX}_headcount", "Headcount"),
    dt(f"{PFX}_startdate", "Start Date", "date"),
    dt(f"{PFX}_duedate", "Due Date", "datetime"),
    pick(f"{PFX}_status", "Status", ["Planned", "Active", "Done"]),
    boolean("project", "isactive", "Is Active"),
])
task = entity("task", "Task", "Tasks", [
    text(f"{PFX}_name", "Name", primary=True),
    decimal(f"{PFX}_hours", "Hours", minv="0"),
    pick(f"{PFX}_priority", "Priority", ["Low", "Medium", "High"]),
    boolean("task", "done", "Done"),
])

APP = f"{PFX}_fullapp"
sitemap_area = lambda e: (
    f'<Area Id="area_{PFX}_{e}" ResourceId="SitemapDesigner.NewTitle" DescriptionResourceId="SitemapDesigner.NewTitle" ShowGroups="true" IntroducedVersion="7.0.0.0">'
    f'<Titles><Title LCID="1033" Title="{e.capitalize()}s" /></Titles>'
    f'<Group Id="group_{PFX}_{e}" ResourceId="SitemapDesigner.NewGroup" DescriptionResourceId="SitemapDesigner.NewGroup" IntroducedVersion="7.0.0.0" IsProfile="false" ToolTipResourseId="SitemapDesigner.Unknown">'
    f'<SubArea Id="subarea_{PFX}_{e}" Icon="/_imgs/imagestrips/transparent_spacer.gif" Entity="{PFX}_{e}" Client="All,Outlook,OutlookLaptopClient,OutlookWorkstationClient,Web" AvailableOffline="true" PassParams="false" Sku="All,OnPremise,Live,SPLA" />'
    f"</Group></Area>"
)

app = f"""<AppModuleSiteMaps><AppModuleSiteMap><SiteMapUniqueName>{APP}</SiteMapUniqueName><EnableCollapsibleGroups>False</EnableCollapsibleGroups>
<ShowHome>True</ShowHome><ShowPinned>True</ShowPinned><ShowRecents>True</ShowRecents>
<SiteMap IntroducedVersion="7.0.0.0">{sitemap_area('project')}{sitemap_area('task')}</SiteMap>
<LocalizedNames><LocalizedName description="Dvgen Full App" languagecode="1033" /></LocalizedNames></AppModuleSiteMap></AppModuleSiteMaps>
<AppModules><AppModule><UniqueName>{APP}</UniqueName><IntroducedVersion>1.0.0.0</IntroducedVersion><WebResourceId>953b9fac-1e5e-e611-80d6-00155ded156f</WebResourceId>
<OptimizedFor></OptimizedFor><statecode>0</statecode><statuscode>1</statuscode><FormFactor>1</FormFactor><ClientType>4</ClientType><NavigationType>0</NavigationType>
<AppModuleComponents><AppModuleComponent type="1" schemaName="{PFX}_project" /><AppModuleComponent type="1" schemaName="{PFX}_task" /><AppModuleComponent type="62" schemaName="{APP}" /></AppModuleComponents>
<AppModuleRoleMaps /><LocalizedNames><LocalizedName description="Dvgen Full App" languagecode="1033" /></LocalizedNames>
<Descriptions><Description description="Test app" languagecode="1033" /></Descriptions>
<appsettings><appsetting settingdefinitionid.uniquename="AppChannel"><iscustomizable>1</iscustomizable><value>1</value></appsetting></appsettings></AppModule></AppModules>"""

write("customizations.xml", f"""<ImportExportXml xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    OrganizationVersion="9.2.26044.164" OrganizationSchemaType="Standard"
    CRMServerServiceabilityVersion="9.2.26044.00164">
<Entities>
{project}
{task}
</Entities>
<optionsets />
<CustomControls />
<EntityDataProviders />
<Languages><Language>1033</Language></Languages>
{app}
</ImportExportXml>
""")

nil1 = "".join(f'<{t} xsi:nil="true"></{t}>' for t in ["City", "County", "Country", "Fax", "FreightTermsCode", "ImportSequenceNumber", "Latitude", "Line1", "Line2", "Line3", "Longitude", "Name", "PostalCode", "PostOfficeBox", "PrimaryContactName"])
nil2 = "".join(f'<{t} xsi:nil="true"></{t}>' for t in ["StateOrProvince", "Telephone1", "Telephone2", "Telephone3", "TimeZoneRuleVersionNumber", "UPSZone", "UTCOffset", "UTCConversionTimeZoneCode"])
addr = lambda n: f"<Address><AddressNumber>{n}</AddressNumber><AddressTypeCode>1</AddressTypeCode>{nil1}<ShippingMethodCode>1</ShippingMethodCode>{nil2}</Address>"

write("solution.xml", f"""<ImportExportXml version="9.2.26044.164" SolutionPackageVersion="9.2" languagecode="1033"
    generatedBy="CrmLive" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    OrganizationVersion="9.2.26044.164" OrganizationSchemaType="Standard"
    CRMServerServiceabilityVersion="9.2.26044.00164">
  <SolutionManifest>
    <UniqueName>DvgenFull</UniqueName>
    <LocalizedNames><LocalizedName description="Dvgen Full" languagecode="1033" /></LocalizedNames>
    <Descriptions/>
    <Version>1.0.0.0</Version>
    <Managed>0</Managed>
    <Publisher>
      <UniqueName>DvgenTestPublisher</UniqueName>
      <LocalizedNames><LocalizedName description="Dvgen Test Publisher" languagecode="1033" /></LocalizedNames>
      <Descriptions/>
      <EMailAddress>dvgen@example.com</EMailAddress>
      <SupportingWebsiteUrl xsi:nil="true"></SupportingWebsiteUrl>
      <CustomizationPrefix>{PFX}</CustomizationPrefix>
      <CustomizationOptionValuePrefix>74913</CustomizationOptionValuePrefix>
      <Addresses>{addr(1)}{addr(2)}</Addresses>
    </Publisher>
    <RootComponents>
      <RootComponent type="1" schemaName="{PFX}_project" behavior="0" />
      <RootComponent type="1" schemaName="{PFX}_task" behavior="0" />
      <RootComponent type="62" schemaName="{APP}" behavior="0" />
      <RootComponent type="80" schemaName="{APP}" behavior="0" />
    </RootComponents>
    <MissingDependencies>
      <MissingDependency>
        <Required type="61" schemaName="msdyn_/Images/AppModule_Default_Icon.png" displayName="msdyn_/Images/AppModule_Default_Icon.png" solution="AppModuleWebResources (2.5)">
          <package appName="AppModule Web Resources Package" version="2.5">AppModuleWebResources (2.5)</package>
        </Required>
        <Dependent type="80" schemaName="{APP}" displayName="Dvgen Full App" />
      </MissingDependency>
      <MissingDependency>
        <Required type="SettingDefinition" displayName="AppChannel" solution="msdyn_AppFrameworkInfraExtensions (1.0.0.16)" id.uniquename="AppChannel">
          <package appName="PowerAppsAppFramework Package" version="1.0.0.25">PowerAppsAppFramework_Anchor (1.0.0.25)</package>
        </Required>
        <Dependent type="AppSetting" displayName="parentappmoduleid.uniquename={APP},settingdefinitionid.uniquename=AppChannel" id.parentappmoduleid.uniquename="{APP}" id.settingdefinitionid.uniquename="AppChannel" />
      </MissingDependency>
    </MissingDependencies>
  </SolutionManifest>
</ImportExportXml>
""")

write("[Content_Types].xml", """<?xml version="1.0" encoding="utf-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="xml" ContentType="application/octet-stream" />
</Types>
""")
print("generated", OUT)
