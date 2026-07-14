# Surrey DevApps V2 Audit - Patch 5.10

Source audited:

`https://services5.arcgis.com/YRpe0VKTJytZSSIB/arcgis/rest/services/Development%20Applications/FeatureServer/0`

Audit date: 2026-06-29

## Verdict

`surrey_devapps_v2` is **CORRECT as an individual development-application layer**, not a generic parcel/subdivision boundary layer.

The layer has populated per-application fields: `PROJECT_NO`, `DESCRIPTION`, `STATUS`, `WEBLINK`, and `APPLICATION_DOCUMENTS_WEBLINK`. The sample rows contain specific application numbers, application narratives, statuses, project portal links, and application-document PDFs.

Important caveat: the layer is not a clean "active only" feed. It contains historical and status-mixed applications, including `Concluded` and `Closed` records. The high row count is therefore explained by record scope: Surrey publishes a broad development-application archive with one geometry row per application/project area, not only current clean future-work leads. This is different from Coquitlam's smaller current development-information feed.

## Field List

- `OBJECTID`
- `PROJECT_NO`
- `DESCRIPTION`
- `STATUS`
- `WEBLINK`
- `APPLICATION_DOCUMENTS_WEBLINK`
- `SHAPE__Area`
- `SHAPE__Length`

## Ten Sample Rows

```json
[
  {
    "OBJECTID": 1,
    "PROJECT_NO": "20-0320-00",
    "DESCRIPTION": "Amend CD Bylaw No. 19823; Development Variance Permit to add small-scale drug stores as an accessory use and to reduce the minimum 400 metre separation distance between a small-scale drug store and an existing drug store.",
    "STATUS": "Concluded",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=20 seq=0320",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7920-0320-00.pdf",
    "SHAPE__Area": 9473.775634765625,
    "SHAPE__Length": 389.57467895258
  },
  {
    "OBJECTID": 2,
    "PROJECT_NO": "20-0321-00",
    "DESCRIPTION": "Rezone a portion of the site from A-2 to IB-2; Development Permit / Development Variance Permit to permit the development of a 10 501 square-metre multi-tenant industrial building.",
    "STATUS": "Concluded",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=20 seq=0321",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7920-0321-00.pdf",
    "SHAPE__Area": 20229.609619140625,
    "SHAPE__Length": 593.4688036253615
  },
  {
    "OBJECTID": 3,
    "PROJECT_NO": "20-0322-00",
    "DESCRIPTION": "Rezoning from Urban Residential (R3) Zone to Small Lot Residential (R4) Zone; Subdivision from one (1) lot into four (4) Small Residential lots; Local Area Plan (LAP) Amendment from Single Family Residential (6 u.p.a.) to Single Family Small Lots; Development Variance Permit (a) the minimum lot width of Type I Corner lots is reduced from 14 metres to 12.71 metres for proposed Lot 3;(b) the minimum lot width requirement for a side-by-side garage or carport is reduced from 13.4 metres to 12.71 metres for proposed Lot 3; (c) the minimum lot width requirement for a side-by-side garage or carport is reduced from 13.4 metres to 12.00 metres for proposed Lot 2 and 4;",
    "STATUS": "Concluded",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=20 seq=0322",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7920-0322-00.pdf",
    "SHAPE__Area": 1546.183349609375,
    "SHAPE__Length": 155.62446134434705
  },
  {
    "OBJECTID": 4,
    "PROJECT_NO": "20-0323-00",
    "DESCRIPTION": "Development Permit to permit partial retention of existing and construction of new onsite directional free standing signs for an existing seniors care community (Elim Village).",
    "STATUS": "Concluded",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=20 seq=0323",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7920-0323-00.pdf",
    "SHAPE__Area": 79573.64990234375,
    "SHAPE__Length": 1198.4886063524661
  },
  {
    "OBJECTID": 5,
    "PROJECT_NO": "20-0325-00",
    "DESCRIPTION": "Rezoning from Suburban Residential Zone (R1) to Comprehensive Development Zone (CD) (based on Urban Residential Zone (R3); Subdivision from one (1) lot into two (2) lots; Official Community Plan (OCP) Amendment from Suburban to Urban to allow subdivision into two single family residential lots and allow the retention of an existing dwelling.",
    "STATUS": "Conditional Approval",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=20 seq=0325",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7920-0325-00.pdf",
    "SHAPE__Area": 1815.66845703125,
    "SHAPE__Length": 170.70280846245663
  },
  {
    "OBJECTID": 6,
    "PROJECT_NO": "20-0326-00",
    "DESCRIPTION": "Rezoning from Urban Residential Zone (R3) to Comprehensive Development Zone (CD) (based on Multiple Residential 70 Zone (RM-70) and Compact Residential Zone (R5); Subdivision from four (4) lots into two (2) lots; Official Community Plan (OCP) Text Amendment to permit a higher density under the Multiple Residential designation over a portion of the subject site; Development Permit to allow the development of a 6-storey residential building containing 169 market strata dwelling units over two levels of underground parking in City Centre as well as a remnant R5 lot.",
    "STATUS": "Conditional Approval",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=20 seq=0326",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7920-0326-00.pdf",
    "SHAPE__Area": 4799.787841796875,
    "SHAPE__Length": 273.2019982096118
  },
  {
    "OBJECTID": 7,
    "PROJECT_NO": "21-0002-00",
    "DESCRIPTION": "Rezoning from RM-D to RF Subdivision from one (1) into three (3) lots.",
    "STATUS": "Referrals",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=21 seq=0002",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7921-0002-00.pdf",
    "SHAPE__Area": 2580.444580078125,
    "SHAPE__Length": 212.59748652073534
  },
  {
    "OBJECTID": 8,
    "PROJECT_NO": "21-0003-00",
    "DESCRIPTION": "Development Variance Permit to allow two additional fascia signs on an existing commercial building.",
    "STATUS": "Concluded",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=21 seq=0003",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7921-0003-00.pdf",
    "SHAPE__Area": 2328.624267578125,
    "SHAPE__Length": 194.66521589586415
  },
  {
    "OBJECTID": 9,
    "PROJECT_NO": "21-0004-00",
    "DESCRIPTION": "Development Variance Permit to reduce the minimum side yard setback to allow for subdivision into two RH lots.",
    "STATUS": "Closed",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=21 seq=0004",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7921-0004-00.pdf",
    "SHAPE__Area": 3762.1064453125,
    "SHAPE__Length": 245.5484124097899
  },
  {
    "OBJECTID": 10,
    "PROJECT_NO": "21-0005-00",
    "DESCRIPTION": "Development Permit to permit the development of two 4-storey and two 5-storey apartment buildings consisting of approximately 390 dwelling units on the northern portion of this site.(Phase Two of 7915-0393-00)",
    "STATUS": "Concluded",
    "WEBLINK": "https://citizenportal.surrey.ca/citizenportal/integration/publicProjectForward.html?year=21 seq=0005",
    "APPLICATION_DOCUMENTS_WEBLINK": "https://cosmos.surrey.ca/geo_ref/Images/DevelopmentApplicationDocuments/PLR_7921-0005-00.pdf",
    "SHAPE__Area": 63721.5478515625,
    "SHAPE__Length": 2583.423256755387
  }
]
```

## Data Integrity Note

Patch 5.10 does not remove this source as a wrong layer. It does flag the status-mixed/historical nature of the feed in the build report so business users do not mistake the 13k+ row volume for 13k+ active near-term projects.
